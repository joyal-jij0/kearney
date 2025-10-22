import { useState } from "react";
import { FileUploadDropZone } from "@/components/FileUploadDropZone";
import { ChatInterface } from "@/components/ChatInterface";

export function AIChat() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState<string | null>(null);

  const handleFileSelect = (file: File, tableNameFromBackend: string) => {
    setSelectedFile(file);
    setTableName(tableNameFromBackend);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setTableName(null);
  };

  return (
    <div className="w-full h-full">
      {!selectedFile ? (
        <div className="flex items-center justify-center min-h-screen bg-linear-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 px-4 py-8">
          <FileUploadDropZone onFileSelect={handleFileSelect} />
        </div>
      ) : (
        <ChatInterface
          fileName={selectedFile.name}
          tableName={tableName || ""}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default AIChat;
