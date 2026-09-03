import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { UploadedDocument } from "@/types";

const PDF_MIME = "application/pdf";

export const useDocumentsStore = defineStore("documents", () => {
  const documents = ref<UploadedDocument[]>([]);

  const hasDocuments = computed(() =>
    documents.value.some((doc) => doc.status === "ready"),
  );

  const readyDocuments = computed(() =>
    documents.value.filter((doc) => doc.status === "ready"),
  );

  function isPdf(file: File): boolean {
    return file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf");
  }

  async function addDocument(file: File): Promise<string | null> {
    if (!isPdf(file)) {
      return "Only PDF files are supported";
    }

    const id = crypto.randomUUID();

    // 1. Initialize directly as "processing"
    documents.value.push({
      id,
      name: file.name,
      size: file.size,
      status: "processing",
    });

    try {
      // TODO: POST /api/documents with FormData when backend is ready
      await new Promise((resolve) => setTimeout(resolve, 800));

      // 2. Find and update the document within documents.value (the reactive proxy array)
      const target = documents.value.find((d) => d.id === id);
      if (target) {
        target.status = "ready";
      }
      return null;
    } catch {
      const target = documents.value.find((d) => d.id === id);
      if (target) {
        target.status = "error";
        target.errorMessage = "Failed to upload document";
      }
      return "Failed to upload document";
    }
  }

  function removeDocument(id: string) {
    documents.value = documents.value.filter((doc) => doc.id !== id);
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
