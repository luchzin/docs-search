import { defineStore } from "pinia";
import { computed } from "vue";
import type { UploadedDocument } from "@/types";
import { useChatStore } from "@/stores/chat";

const PDF_MIME = "application/pdf";

export const useDocumentsStore = defineStore("documents", () => {
  const chatStore = useChatStore();

  const documents = computed<UploadedDocument[]>(() => {
    return chatStore.activeChat?.documents || [];
  });

  const hasDocuments = computed(() =>
    documents.value.some((doc) => doc.status === "ready")
  );

  const readyDocuments = computed(() =>
    documents.value.filter((doc) => doc.status === "ready")
  );

  function isPdf(file: File): boolean {
    return file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf");
  }

  async function addDocument(file: File): Promise<string | null> {
    if (!isPdf(file)) {
      return "Only PDF files are supported";
    }

    let activeChat = chatStore.activeChat;
    if (!activeChat) {
      const newId = chatStore.createNewChat();
      activeChat = chatStore.chats.find((c) => c.id === newId);
    }

    if (!activeChat) {
      return "Failed to create or access active chat session";
    }

    const id = crypto.randomUUID();

    const newDoc: UploadedDocument = {
      id,
      name: file.name,
      size: file.size,
      status: "processing",
    };

    activeChat.documents.push(newDoc);
    activeChat.updated_at = new Date().toISOString();
    chatStore.saveToStorage();

    try {
      // TODO: POST /api/documents with FormData when backend is ready
      await new Promise((resolve) => setTimeout(resolve, 800));

      const target = activeChat.documents.find((d) => d.id === id);
      if (target) {
        target.status = "ready";
      }
      chatStore.saveToStorage();
      return null;
    } catch {
      const target = activeChat.documents.find((d) => d.id === id);
      if (target) {
        target.status = "error";
        target.errorMessage = "Failed to upload document";
      }
      chatStore.saveToStorage();
      return "Failed to upload document";
    }
  }

  function removeDocument(id: string) {
    const activeChat = chatStore.activeChat;
    if (activeChat) {
      activeChat.documents = activeChat.documents.filter((doc) => doc.id !== id);
      activeChat.updated_at = new Date().toISOString();
      chatStore.saveToStorage();
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return {
    documents,
    hasDocuments,
    readyDocuments,
    addDocument,
    removeDocument,
    formatFileSize,
    isPdf,
  };
});
