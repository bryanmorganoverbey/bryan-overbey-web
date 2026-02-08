"use client";

import React from "react";

interface ProcessingStatusProps {
  status: "idle" | "uploading" | "processing" | "complete" | "error";
  fileName?: string;
  error?: string;
  uploadProgress?: number;
  onDownload?: () => void;
  onReset?: () => void;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  status,
  fileName,
  error,
  uploadProgress = 0,
  onDownload,
  onReset,
}) => {
  if (status === "idle") {
    return null;
  }

  return (
    <div className="mt-8 p-6 bg-white rounded-lg shadow-md">
      {fileName && (
        <div className="mb-4">
          <p className="text-sm text-gray-600">File:</p>
          <p className="font-medium text-gray-800 truncate">{fileName}</p>
        </div>
      )}

      <div className="flex flex-col items-center space-y-4">
        {status === "uploading" && (
          <div className="w-full max-w-md">
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Uploading...
                </span>
                <span className="text-sm font-medium text-blue-600">
                  {uploadProgress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
            <p className="text-sm text-gray-500 text-center">
              Please wait while your file uploads...
            </p>
          </div>
        )}

        {status === "processing" && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-lg font-medium text-gray-700">
              Processing PDF...
            </p>
            <p className="text-sm text-gray-500">
              Sorting receipts by vehicle VIN. This may take a moment.
            </p>
          </>
        )}

        {status === "complete" && (
          <>
            <svg
              className="w-16 h-16 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-lg font-medium text-green-600">
              Processing Complete!
            </p>
            <p className="text-sm text-gray-500">
              Your sorted PDF is ready to download
            </p>

            <button
              onClick={onDownload}
              className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                       transition-colors duration-200 font-medium flex items-center space-x-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              <span>Download Sorted PDF</span>
            </button>

            <button
              onClick={onReset}
              className="mt-2 px-4 py-2 text-gray-600 hover:text-gray-800
                       transition-colors duration-200 text-sm"
            >
              Process another file
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <svg
              className="w-16 h-16 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-lg font-medium text-red-600">
              Processing Failed
            </p>
            <p className="text-sm text-gray-600 text-center max-w-md">
              {error ||
                "An error occurred while processing your file. Please try again."}
            </p>

            <button
              onClick={onReset}
              className="mt-4 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700
                       transition-colors duration-200 font-medium"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default ProcessingStatus;
