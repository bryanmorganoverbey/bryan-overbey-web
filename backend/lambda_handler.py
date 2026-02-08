#!/usr/bin/env python3
"""
AWS Lambda handler for Fuel Receipt Sorter API.
Wraps the Flask application for serverless execution.
"""

import os
import json
import base64
import tempfile
import time
import logging
from typing import Dict, Any

import boto3  # pylint: disable=import-error
from botocore.exceptions import ClientError  # pylint: disable=import-error

from sort_fuel_receipts_ocr import sort_pdf_by_vehicle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client("s3")
TEMP_BUCKET = os.environ.get("TEMP_BUCKET", "")


def validate_pdf_magic_number(file_path: str) -> bool:
    """Validate that file is actually a PDF by checking magic number."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception:
        return False


def upload_to_s3(file_path: str, s3_key: str) -> str:
    """Upload a file to S3 and return the S3 URI."""
    try:
        s3_client.upload_file(file_path, TEMP_BUCKET, s3_key)
        return f"s3://{TEMP_BUCKET}/{s3_key}"
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise


def download_from_s3(s3_key: str, local_path: str) -> None:
    """Download a file from S3."""
    try:
        s3_client.download_file(TEMP_BUCKET, s3_key, local_path)
    except ClientError as e:
        logger.error(f"Failed to download from S3: {e}")
        raise


def delete_from_s3(s3_key: str) -> None:
    """Delete a file from S3."""
    try:
        s3_client.delete_object(Bucket=TEMP_BUCKET, Key=s3_key)
    except ClientError as e:
        logger.warning(f"Failed to delete from S3: {e}")


def create_response(
    status_code: int,
    body: Any,
    content_type: str = "application/json",
    is_base64: bool = False,
) -> Dict[str, Any]:
    """Create an API Gateway response."""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
    }

    if is_base64:
        response["body"] = body
        response["isBase64Encoded"] = True
    else:
        response["body"] = json.dumps(body) if isinstance(body, dict) else body

    return response


def handle_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle health check endpoint."""
    return create_response(
        200,
        {
            "status": "healthy",
            "version": "1.0.0",
            "service": "fuel-receipt-sorter-lambda",
        },
    )


def handle_process(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle PDF processing endpoint."""
    try:
        # Get the body
        body = event.get("body", "")
        is_base64 = event.get("isBase64Encoded", False)

        if is_base64:
            body = base64.b64decode(body)
        elif isinstance(body, str):
            body = body.encode("utf-8")

        # Parse multipart form data
        content_type = ""
        headers = event.get("headers", {})
        for key, value in headers.items():
            if key.lower() == "content-type":
                content_type = value
                break

        if "multipart/form-data" not in content_type:
            return create_response(400, {"error": "Expected multipart/form-data"})

        # Extract boundary
        boundary = None
        for part in content_type.split(";"):
            part = part.strip()
            if part.startswith("boundary="):
                boundary = part[9:].strip('"')
                break

        if not boundary:
            return create_response(400, {"error": "No boundary in multipart data"})

        # Parse multipart data
        file_data = parse_multipart(body, boundary)

        if not file_data:
            return create_response(400, {"error": "No file provided"})

        # Get optional OCR parameter
        query_params = event.get("queryStringParameters") or {}
        use_ocr = query_params.get("use_ocr", "false").lower() == "true"

        # Create temp files
        timestamp = int(time.time())
        temp_dir = tempfile.gettempdir()

        input_filename = f"{timestamp}_input.pdf"
        output_filename = f"{timestamp}_sorted.pdf"

        input_path = os.path.join(temp_dir, input_filename)
        output_path = os.path.join(temp_dir, output_filename)

        try:
            # Save uploaded file
            with open(input_path, "wb") as f:
                f.write(file_data)

            logger.info(f"Saved input file: {input_path}, size: {len(file_data)} bytes")

            # Validate PDF
            if not validate_pdf_magic_number(input_path):
                return create_response(400, {"error": "Invalid PDF file format"})

            # Process the PDF
            logger.info(f"Processing PDF (OCR: {use_ocr})")
            sort_pdf_by_vehicle(
                input_pdf_path=input_path,
                output_pdf_path=output_path,
                use_ocr=use_ocr,
            )

            # Check if output was created
            if not os.path.exists(output_path):
                return create_response(500, {"error": "Failed to generate sorted PDF"})

            # Read output file
            with open(output_path, "rb") as f:
                output_data = f.read()

            logger.info(
                f"Successfully processed PDF, output size: {len(output_data)} bytes"
            )

            # Return the processed PDF as base64
            return create_response(
                200,
                base64.b64encode(output_data).decode("utf-8"),
                content_type="application/pdf",
                is_base64=True,
            )

        finally:
            # Cleanup temp files
            for path in [input_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {path}: {e}")

    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return create_response(500, {"error": f"Processing failed: {str(e)}"})


def parse_multipart(body: bytes, boundary: str) -> bytes:
    """Parse multipart form data and extract file content."""
    boundary_bytes = f"--{boundary}".encode("utf-8")
    parts = body.split(boundary_bytes)

    for part in parts:
        if b"filename=" not in part:
            continue

        # Find the content after headers (double CRLF)
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        content = part[header_end + 4 :]

        # Remove trailing boundary markers
        if content.endswith(b"\r\n"):
            content = content[:-2]
        if content.endswith(b"--"):
            content = content[:-2]
        if content.endswith(b"\r\n"):
            content = content[:-2]

        return content

    return b""


def handle_upload_url(_event: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a presigned URL for uploading a file to S3."""
    try:
        timestamp = int(time.time())
        upload_key = f"uploads/{timestamp}_{os.urandom(8).hex()}.pdf"

        # Generate presigned URL for upload (valid for 10 minutes)
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": TEMP_BUCKET,
                "Key": upload_key,
                "ContentType": "application/pdf",
            },
            ExpiresIn=600,
        )

        return create_response(
            200,
            {
                "uploadUrl": presigned_url,
                "key": upload_key,
            },
        )
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}", exc_info=True)
        return create_response(
            500, {"error": f"Failed to generate upload URL: {str(e)}"}
        )


def handle_process_s3(event: Dict[str, Any]) -> Dict[str, Any]:
    """Process a PDF that was uploaded to S3."""
    try:
        # Parse the request body
        body = event.get("body", "{}")
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body).decode("utf-8")

        data = json.loads(body) if isinstance(body, str) else body
        input_key = data.get("key")

        if not input_key:
            return create_response(400, {"error": "Missing 'key' parameter"})

        # Get optional OCR parameter
        use_ocr = data.get("use_ocr", False)

        # Create temp files
        timestamp = int(time.time())
        temp_dir = tempfile.gettempdir()

        input_path = os.path.join(temp_dir, f"{timestamp}_input.pdf")
        output_path = os.path.join(temp_dir, f"{timestamp}_sorted.pdf")
        output_key = f"processed/{timestamp}_{os.urandom(8).hex()}_sorted.pdf"

        try:
            # Download input file from S3
            logger.info(f"Downloading from S3: {input_key}")
            download_from_s3(input_key, input_path)

            # Validate PDF
            if not validate_pdf_magic_number(input_path):
                return create_response(400, {"error": "Invalid PDF file format"})

            # Process the PDF
            logger.info(f"Processing PDF (OCR: {use_ocr})")
            sort_pdf_by_vehicle(
                input_pdf_path=input_path,
                output_pdf_path=output_path,
                use_ocr=use_ocr,
            )

            # Check if output was created
            if not os.path.exists(output_path):
                return create_response(500, {"error": "Failed to generate sorted PDF"})

            # Upload result to S3
            logger.info(f"Uploading result to S3: {output_key}")
            upload_to_s3(output_path, output_key)

            # Generate presigned URL for download (valid for 1 hour)
            download_url = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": TEMP_BUCKET,
                    "Key": output_key,
                },
                ExpiresIn=3600,
            )

            # Clean up input file from S3
            delete_from_s3(input_key)

            logger.info("Successfully processed PDF")
            return create_response(
                200,
                {
                    "downloadUrl": download_url,
                    "key": output_key,
                },
            )

        finally:
            # Cleanup temp files
            for path in [input_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {path}: {e}")

    except Exception as e:
        logger.error(f"Error processing PDF from S3: {e}", exc_info=True)
        return create_response(500, {"error": f"Processing failed: {str(e)}"})


def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Main Lambda handler."""
    logger.info(f"Received event: {json.dumps(event, default=str)[:500]}")

    # Handle OPTIONS for CORS
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if not http_method:
        http_method = event.get("httpMethod", "GET")

    if http_method == "OPTIONS":
        return create_response(200, {})

    # Get the path
    path = event.get("rawPath", "")
    if not path:
        path = event.get("path", "")

    logger.info(f"Method: {http_method}, Path: {path}")

    # Route to appropriate handler
    if path.endswith("/health") or path == "/api/health":
        return handle_health(event)
    elif path.endswith("/upload-url") or path == "/api/upload-url":
        return handle_upload_url(event)
    elif path.endswith("/process-s3") or path == "/api/process-s3":
        if http_method == "POST":
            return handle_process_s3(event)
        else:
            return create_response(405, {"error": "Method not allowed"})
    elif path.endswith("/process") or path == "/api/process":
        if http_method == "POST":
            return handle_process(event)
        else:
            return create_response(405, {"error": "Method not allowed"})
    else:
        return create_response(404, {"error": "Not found"})
