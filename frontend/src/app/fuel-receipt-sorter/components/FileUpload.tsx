"use client";

import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, disabled }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];

        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
          alert(
            `File is ${sizeMB}MB. Maximum size is 100MB. Please compress or split your PDF.`
          );
          return;
        }

        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: {
        "application/pdf": [".pdf"],
      },
      multiple: false,
      disabled,
    });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
        transition-all duration-200 ease-in-out
        ${isDragActive && !isDragReject ? "border-blue-500 bg-blue-50" : ""}
        ${isDragReject ? "border-red-500 bg-red-50" : ""}
        ${!isDragActive && !isDragReject ? "border-gray-300 hover:border-blue-400 hover:bg-gray-50" : ""}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center space-y-4">
        <svg
          className={`w-16 h-16 ${isDragActive ? "text-blue-500" : "text-gray-400"}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        <div>
          {isDragActive ? (
            <p className="text-lg font-medium text-blue-600">
              Drop the PDF file here
            </p>
          ) : isDragReject ? (
            <p className="text-lg font-medium text-red-600">
              Please upload a PDF file only
            </p>
          ) : (
            <>
              <p className="text-lg font-medium text-gray-700">
                Drag and drop your PDF file here
              </p>
              <p className="text-sm text-gray-500 mt-2">or click to browse</p>
            </>
          )}
        </div>

        <div className="text-center">
          <p className="text-xs text-gray-400">Maximum file size: 100MB</p>
          <p className="text-xs text-amber-600 mt-1">
            Files over 20MB may take several minutes to upload
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
