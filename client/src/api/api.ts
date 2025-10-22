import axios from "axios";

const api = axios.create({
  baseURL: process.env.BUN_PUBLIC_BASE_URL,
  headers: {
    Accept: "application/json",
  },
});

export interface UploadResponse {
  table_name: string;
  rows_count: number;
  columns: string[];
  [key: string]: any;
}

export interface ChatResponse {
  response: string;
  [key: string]: any;
}

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<UploadResponse>(
    "/api/v1/files/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};

export interface ChatResponse {
  status_code: number;
  data: {
    answer: string;
    function_calls: any[];
    model: string;
  };
  message: string;
  success: boolean;
}

export const sendChatMessage = async (
  question: string,
  tableName: string
): Promise<{ response: string }> => {
  const response = await api.post<ChatResponse>("/api/v1/chat/", {
    question,
    table_name: tableName,
  });

  return {
    response: response.data.data.answer,
  };
};

export default api;
