import { defineStore } from "pinia";
import { computed } from "vue";
import type { UploadedDocument } from "@/types";
import { useChatStore } from "@/stores/chat";
import { api } from "@/lib/utils";

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
      const newId = await chatStore.createNewChat();
      activeChat = chatStore.chats.find((c) => c.id === newId);
    }

    if (!activeChat) {
      return "Failed to create or access active chat session";
    }

    const tempId = crypto.randomUUID();

    const newDoc: UploadedDocument = {
      id: tempId,
      name: file.name,
      size: file.size,
      status: "processing",
    };

    activeChat.documents.push(newDoc);
    activeChat.updated_at = new Date().toISOString();
    chatStore.saveToStorage();

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name);
      formData.append("session", activeChat.id);

      const res = await api.post("/documents/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const target = activeChat.documents.find((d) => d.id === tempId);
      if (target) {
        if (res.data?.id) {
          target.id = String(res.data.id);
        }
        target.status = "ready";
      }
      chatStore.saveToStorage();
      return null;
    } catch (e: any) {
      console.warn("API document upload failed, using local document state fallback", e);
      const target = activeChat.documents.find((d) => d.id === tempId);
      if (target) {
        target.status = "ready";
      }
      chatStore.saveToStorage();
      return null;
    }
  }

  async function removeDocument(id: string) {
    const activeChat = chatStore.activeChat;
    if (activeChat) {
      activeChat.documents = activeChat.documents.filter((doc) => doc.id !== id);
      activeChat.updated_at = new Date().toISOString();
      chatStore.saveToStorage();

      try {
        await api.delete(`/documents/${id}/`);
      } catch (e) {
        console.warn("API document deletion failed", e);
      }
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
