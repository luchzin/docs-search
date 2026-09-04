import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Chat, ChatMessage } from "@/types";
import { useDocumentsStore } from "@/stores/documents";

const STORAGE_CHATS_KEY = "doc_search_chats";
const STORAGE_ACTIVE_KEY = "doc_search_active_chat_id";

export const useChatStore = defineStore("chat", () => {
  const chats = ref<Chat[]>([]);
  const activeChatId = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Load state from localStorage on init
  loadFromStorage();

  const activeChat = computed(() =>
    chats.value.find((c) => c.id === activeChatId.value)
  );

  const messages = computed(() => activeChat.value?.messages || []);

  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_CHATS_KEY, JSON.stringify(chats.value));
      if (activeChatId.value) {
        localStorage.setItem(STORAGE_ACTIVE_KEY, activeChatId.value);
      } else {
        localStorage.removeItem(STORAGE_ACTIVE_KEY);
      }
    } catch (e) {
      console.error("Failed to save chats to storage", e);
    }
  }

  function loadFromStorage() {
    try {
      const storedChats = localStorage.getItem(STORAGE_CHATS_KEY);
      const storedActiveId = localStorage.getItem(STORAGE_ACTIVE_KEY);
      if (storedChats) {
        const parsed: Chat[] = JSON.parse(storedChats);
        chats.value = parsed.map((c) => ({
          ...c,
          messages: c.messages || [],
          documents: c.documents || [],
        }));
      }
      if (storedActiveId && chats.value.some((c) => c.id === storedActiveId)) {
        activeChatId.value = storedActiveId;
      } else if (chats.value.length > 0) {
        activeChatId.value = chats.value[0].id;
      }
    } catch (e) {
      console.error("Failed to load chats from storage", e);
      chats.value = [];
      activeChatId.value = null;
    }
  }

  function createNewChat(): string {
    const newChat: Chat = {
      id: crypto.randomUUID(),
      title: "New chat",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [],
      documents: [],
    };
    chats.value.unshift(newChat);
    activeChatId.value = newChat.id;
    error.value = null;
    saveToStorage();
    return newChat.id;
  }

  function selectChat(id: string) {
    if (chats.value.some((c) => c.id === id)) {
      activeChatId.value = id;
      error.value = null;
      saveToStorage();
    }
  }

  function renameChat(id: string, newTitle: string) {
    const chatItem = chats.value.find((c) => c.id === id);
    if (chatItem) {
      const trimmed = newTitle.trim();
      chatItem.title = trimmed || "Untitled chat";
      chatItem.updated_at = new Date().toISOString();
      saveToStorage();
    }
  }

  function deleteChat(id: string) {
    chats.value = chats.value.filter((c) => c.id !== id);
    if (activeChatId.value === id) {
      activeChatId.value = chats.value[0]?.id || null;
    }
    saveToStorage();
  }

  function clearMessages() {
    if (activeChat.value) {
      activeChat.value.messages = [];
      activeChat.value.updated_at = new Date().toISOString();
      saveToStorage();
    }
    error.value = null;
  }

  async function sendMessage(content: string) {
    const trimmed = content.trim();
    if (!trimmed || isLoading.value) return;

    const documentsStore = useDocumentsStore();

    if (!documentsStore.hasDocuments) {
      error.value = "Please upload at least one PDF document to this chat first";
      return;
    }

    error.value = null;

    let targetChat = activeChat.value;
    if (!targetChat) {
      const newId = createNewChat();
      targetChat = chats.value.find((c) => c.id === newId);
    }

    if (!targetChat) return;

    // Auto generate title if title is default "New chat"
    if (targetChat.title.toLowerCase() === "new chat" && targetChat.messages.length === 0) {
      const generatedTitle = trimmed.length > 30 ? `${trimmed.slice(0, 30)}...` : trimmed;
      targetChat.title = generatedTitle;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    targetChat.messages.push(userMessage);
    targetChat.updated_at = new Date().toISOString();
    saveToStorage();

    isLoading.value = true;

    try {
      // TODO: Replace with streaming RAG API call
      await new Promise((resolve) => setTimeout(resolve, 1200));

      const docNames = documentsStore.readyDocuments
        .map((doc) => doc.name)
        .join(", ");

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Based on your documents (${docNames}), here is a response to: "${trimmed}"\n\nThis is a placeholder answer. Connect the backend RAG pipeline to retrieve real answers from your PDFs.`,
        createdAt: new Date().toISOString(),
      };

      targetChat.messages.push(assistantMessage);
      targetChat.updated_at = new Date().toISOString();
      saveToStorage();
    } catch {
      error.value = "Failed to get a response. Please try again.";
    } finally {
      isLoading.value = false;
    }
  }

  return {
    chats,
    activeChatId,
    activeChat,
    messages,
    isLoading,
    error,
    createNewChat,
    selectChat,
    renameChat,
    deleteChat,
    sendMessage,
    clearMessages,
    saveToStorage,
  };
});
