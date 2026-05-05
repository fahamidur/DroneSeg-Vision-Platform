"use client";

import { UploadCloud } from "lucide-react";
import { FileRejection, useDropzone } from "react-dropzone";

interface UploadDropzoneProps {
  onFile: (file: File) => void;
  onError?: (message: string) => void;
  disabled?: boolean;
}

function rejectionMessage(rejections: FileRejection[]): string {
  const first = rejections[0];

  if (!first) {
    return "The image could not be uploaded.";
  }

  const error = first.errors[0];

  if (!error) {
    return "The selected file was rejected.";
  }

  if (error.code === "file-too-large") {
    return "The selected image is larger than 50 MB. Please compress it and try again.";
  }

  if (error.code === "file-invalid-type") {
    return "Unsupported file type. Please upload JPG, PNG, WebP, BMP or TIFF. Convert HEIC or AVIF to JPG first.";
  }

  return error.message || "The selected file was rejected.";
}

export function UploadDropzone({ onFile, onError, disabled = false }: UploadDropzoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "image/jpeg": [".jpg", ".jpeg", ".JPG", ".JPEG"],
      "image/png": [".png", ".PNG"],
      "image/webp": [".webp", ".WEBP"],
      "image/bmp": [".bmp", ".BMP"],
      "image/tiff": [".tif", ".tiff", ".TIF", ".TIFF"],
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024,
    disabled,
    onDropAccepted: (files) => {
      if (files[0]) {
        onFile(files[0]);
      }
    },
    onDropRejected: (rejections) => {
      onError?.(rejectionMessage(rejections));
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-2xl border border-dashed p-5 text-center transition ${
        isDragActive
          ? "border-emerald-500 bg-emerald-50"
          : "border-slate-300 bg-white/75 hover:border-sky-400 hover:bg-sky-50"
      } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <input {...getInputProps()} />
      <UploadCloud className="mx-auto mb-2 h-7 w-7 text-sky-600" />
      <p className="text-sm font-semibold text-slate-800">Drop a drone image here</p>
      <p className="mt-1 text-xs text-slate-500">
        JPG, PNG, WebP, BMP or TIFF, up to 50 MB
      </p>
      <p className="mt-1 text-[11px] text-slate-400">
        HEIC and AVIF should be converted to JPG first
      </p>
    </div>
  );
}
