export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface Chat {
  id: string;
  title: string;
  updated_at: string;
  created_at: string;
  messages: ChatMessage[];
  documents: UploadedDocument[];
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
