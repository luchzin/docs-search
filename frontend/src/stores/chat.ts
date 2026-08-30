import { defineStore } from "pinia"
import { ref } from "vue"
import type { ChatMessage } from "@/types"
import { useDocumentsStore } from "@/stores/documents"

export const useChatStore = defineStore("chat", () => {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function sendMessage(content: string) {
    const trimmed = content.trim()
    if (!trimmed || isLoading.value) return

    const documentsStore = useDocumentsStore()
    if (!documentsStore.hasDocuments) {
      error.value = "Please upload at least one PDF document first"
      return
    }

    error.value = null
    messages.value.push({
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: new Date(),
    })

    isLoading.value = true

    try {
      // TODO: Replace with streaming RAG API call
      await new Promise((resolve) => setTimeout(resolve, 1200))

      const docNames = documentsStore.readyDocuments
        .map((doc) => doc.name)
        .join(", ")

      messages.value.push({
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Based on your documents (${docNames}), here is a response to: "${trimmed}"\n\nThis is a placeholder answer. Connect the backend RAG pipeline to retrieve real answers from your PDFs.`,
        createdAt: new Date(),
      })
    } catch {
      error.value = "Failed to get a response. Please try again."
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    error.value = null
  }

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  }
})
