# Use AWS Lambda Python 3.11 base image (Amazon Linux 2)
FROM public.ecr.aws/lambda/python:3.11-arm64

# Install system dependencies for Tesseract OCR and Poppler
# Skip yum update to avoid disk space issues, install directly
RUN yum install -y \
    tesseract \
    poppler-utils \
    && yum clean all \
    && rm -rf /var/cache/yum/*

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY sort_fuel_receipts_ocr.py ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["lambda_handler.handler"]
