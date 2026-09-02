export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: Date;
}
export interface User {
  id: string;
  username: string;
  email: string;
  password?: string;
  created_at?: string;
}
export type DocumentStatus = "uploading" | "processing" | "ready" | "error";

export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  status: DocumentStatus;
  errorMessage?: string;
}
