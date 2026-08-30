export type MessageRole = "user" | "assistant"

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  createdAt: Date
}

export type DocumentStatus = "uploading" | "processing" | "ready" | "error"

export interface UploadedDocument {
  id: string
  name: string
  size: number
  status: DocumentStatus
  errorMessage?: string
}
