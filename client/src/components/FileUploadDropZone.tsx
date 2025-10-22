import { useRef, useState } from "react";
import { Upload, X, File, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { uploadFile } from "@/api/api";

interface FileUploadDropZoneProps {
  onFileSelect: (file: File, tableName: string) => void;
}

export function FileUploadDropZone({ onFileSelect }: FileUploadDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const isValidFile = (file: File) => {
    const validTypes = [
      "text/csv",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];
    return (
      validTypes.includes(file.type) ||
      file.name.endsWith(".csv") ||
      file.name.endsWith(".xlsx") ||
      file.name.endsWith(".xls")
    );
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadFile(file);
      onFileSelect(file, response.table_name);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to upload file";
      setError(errorMessage);
      setSelectedFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file && isValidFile(file)) {
        setSelectedFile(file);
        setError(null);
        handleUpload(file);
      } else {
        setError("Please upload a valid CSV or Excel file");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file && isValidFile(file)) {
        setSelectedFile(file);
        setError(null);
        handleUpload(file);
      } else {
        setError("Please upload a valid CSV or Excel file");
        setSelectedFile(null);
      }
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          AI Data Chat
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload a CSV or Excel file to start asking questions about your data
        </p>
      </div>

      {!selectedFile && !isUploading ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-12 transition-colors cursor-pointer",
            isDragging
              ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
              : "border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-900/70"
          )}
        >
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Upload className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Drag and drop your file here
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                or click to browse
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                CSV or Excel (.xlsx, .xls) files are supported
              </p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
            className="hidden"
            onClick={(e) => {
              e.currentTarget.click();
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="absolute inset-0 w-full h-full cursor-pointer"
          />
        </div>
      ) : isUploading ? (
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">
                  Uploading {selectedFile?.name}...
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Processing your file
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
                  <File className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {selectedFile?.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedFile && (selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClear}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              File uploaded successfully! Click below to start chatting.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900 dark:text-red-400 text-sm">
              Error uploading file
            </p>
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
