"use client";

import { useState } from "react";
import axios from "axios";
import Link from "next/link";
import FileUpload from "./components/FileUpload";
import ProcessingStatus from "./components/ProcessingStatus";

type Status = "idle" | "uploading" | "processing" | "complete" | "error";

const API_BASE_URL = process.env.NEXT_PUBLIC_FUEL_SORTER_API_URL ?? "";

export default function FuelReceiptSorter() {
  const [status, setStatus] = useState<Status>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>("");
  const [processedFileBlob, setProcessedFileBlob] = useState<Blob | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setStatus("uploading");
    setError("");
    setUploadProgress(0);

    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > 20) {
      const proceed = window.confirm(
        `This file is ${fileSizeMB.toFixed(1)}MB. Large files may take several minutes to upload and process. Continue?`
      );
      if (!proceed) {
        setStatus("idle");
        return;
      }
    }

    try {
      // Step 1: Get presigned upload URL
      const uploadUrlResponse = await axios.get(
        `${API_BASE_URL}/api/upload-url`
      );
      const { uploadUrl, key } = uploadUrlResponse.data;

      // Step 2: Upload file directly to S3
      await axios.put(uploadUrl, file, {
        headers: {
          "Content-Type": "application/pdf",
        },
        timeout: 300000,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);

            if (percentCompleted === 100) {
              setStatus("processing");
            }
          }
        },
      });

      // Step 3: Trigger processing
      const processResponse = await axios.post(
        `${API_BASE_URL}/api/process-s3`,
        {
          key: key,
          use_ocr: false,
        },
        {
          timeout: 300000,
        }
      );

      // Step 4: Download the processed file
      const downloadResponse = await axios.get(
        processResponse.data.downloadUrl,
        {
          responseType: "blob",
        }
      );

      setProcessedFileBlob(downloadResponse.data);
      setStatus("complete");
    } catch (err: unknown) {
      console.error("Error processing file:", err);

      let errorMessage =
        "An error occurred while processing your file. Please try again.";

      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status === 400) {
          errorMessage =
            "Invalid file format. Please upload a valid PDF file.";
        } else if (err.response.status === 413) {
          errorMessage = "File is too large. Maximum size is 100MB.";
        } else if (err.response.status === 500) {
          errorMessage =
            "Server error while processing the file. Please check the file format.";
        }
        if (err.response.data?.error) {
          errorMessage = err.response.data.error;
        }
      } else if (axios.isAxiosError(err) && err.request) {
        errorMessage =
          "Connection failed. Please check your internet connection and try again.";
      }

      setError(errorMessage);
      setStatus("error");
    }
  };

  const handleDownload = () => {
    if (!processedFileBlob || !selectedFile) return;

    const url = window.URL.createObjectURL(processedFileBlob);
    const link = document.createElement("a");
    link.href = url;

    const originalName = selectedFile.name.replace(".pdf", "");
    link.download = `${originalName}_sorted.pdf`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setStatus("idle");
    setSelectedFile(null);
    setError("");
    setProcessedFileBlob(null);
    setUploadProgress(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      <div className="container mx-auto px-4 py-12">
        {/* Back link */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-blue-600 hover:text-blue-800 transition-colors text-sm font-medium"
          >
            &larr; Back to Home
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Fuel Receipt Sorter
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your fuel receipt PDF and we&apos;ll automatically sort the
            pages by vehicle VIN. Perfect for organizing fleet fuel receipts.
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-3xl mx-auto">
          {status === "idle" && (
            <FileUpload
              onFileSelect={handleFileSelect}
              disabled={status !== "idle"}
            />
          )}

          <ProcessingStatus
            status={status}
            fileName={selectedFile?.name}
            error={error}
            uploadProgress={uploadProgress}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        </div>

        {/* Features */}
        {status === "idle" && (
          <div className="mt-16 max-w-4xl mx-auto">
            <h2 className="text-2xl font-semibold text-gray-800 text-center mb-8">
              Features
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">
                  Fast Processing
                </h3>
                <p className="text-gray-600 text-sm">
                  Quickly sorts receipts by vehicle VIN using advanced OCR
                  technology
                </p>
              </div>

              <div className="text-center">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">
                  Secure &amp; Private
                </h3>
                <p className="text-gray-600 text-sm">
                  Files are processed securely and deleted immediately after
                  download
                </p>
              </div>

              <div className="text-center">
                <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-purple-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">
                  Smart Recognition
                </h3>
                <p className="text-gray-600 text-sm">
                  Handles both standard PDFs and custom-encoded receipts with OCR
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
