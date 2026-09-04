import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Chat, ChatMessage } from "@/types";
import { useDocumentsStore } from "@/stores/documents";
import { api } from "@/lib/utils";

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

  async function fetchChats() {
    try {
      const res = await api.get<any[]>("/chat/");
      if (Array.isArray(res.data)) {
        chats.value = res.data.map((c) => ({
          id: String(c.id),
          title: c.title || "Untitled chat",
          created_at: c.created_at,
          updated_at: c.updated_at,
          messages: (c.messages || []).map((m: any) => ({
            id: String(m.id),
            role: m.role,
            content: m.content,
            createdAt: m.created_at || m.createdAt,
          })),
          documents: (c.documents || []).map((d: any) => ({
            id: String(d.id),
            name: d.title || (d.file ? d.file.split("/").pop() : "Document"),
            size: 0,
            status: "ready",
          })),
        }));

        if (!activeChatId.value || !chats.value.some((c) => c.id === activeChatId.value)) {
          activeChatId.value = chats.value[0]?.id || null;
        }
        saveToStorage();
      }
    } catch (e) {
      console.warn("Django API unreachable or unauthorized; using local cache", e);
    }
  }

  async function createNewChat(title: string = "New chat"): Promise<string> {
    const tempId = crypto.randomUUID();
    const newChat: Chat = {
      id: tempId,
      title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [],
      documents: [],
    };
    chats.value.unshift(newChat);
    activeChatId.value = newChat.id;
    error.value = null;
    saveToStorage();

    try {
      const res = await api.post("/chat/", { title });
      if (res.data?.id) {
        newChat.id = String(res.data.id);
        newChat.created_at = res.data.created_at || newChat.created_at;
        newChat.updated_at = res.data.updated_at || newChat.updated_at;
        activeChatId.value = newChat.id;
        saveToStorage();
      }
    } catch (e) {
      console.warn("Could not sync new chat with API", e);
    }

    return newChat.id;
  }

  function selectChat(id: string) {
    if (chats.value.some((c) => c.id === id)) {
      activeChatId.value = id;
      error.value = null;
      saveToStorage();
    }
  }

  async function renameChat(id: string, newTitle: string) {
    const chatItem = chats.value.find((c) => c.id === id);
    if (chatItem) {
      const trimmed = newTitle.trim() || "Untitled chat";
      chatItem.title = trimmed;
      chatItem.updated_at = new Date().toISOString();
      saveToStorage();

      try {
        await api.patch(`/chat/${id}/`, { title: trimmed });
      } catch (e) {
        console.warn("Failed to rename chat on API", e);
      }
    }
  }

  async function deleteChat(id: string) {
    chats.value = chats.value.filter((c) => c.id !== id);
    if (activeChatId.value === id) {
      activeChatId.value = chats.value[0]?.id || null;
    }
    saveToStorage();

    try {
      await api.delete(`/chat/${id}/`);
    } catch (e) {
      console.warn("Failed to delete chat on API", e);
    }
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
      const newId = await createNewChat();
      targetChat = chats.value.find((c) => c.id === newId);
    }

    if (!targetChat) return;

    // Auto generate title if title is default "New chat"
    if (targetChat.title.toLowerCase() === "new chat" && targetChat.messages.length === 0) {
      const generatedTitle = trimmed.length > 30 ? `${trimmed.slice(0, 30)}...` : trimmed;
      renameChat(targetChat.id, generatedTitle);
    }

    const tempUserMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    targetChat.messages.push(tempUserMsg);
    targetChat.updated_at = new Date().toISOString();
    saveToStorage();

    isLoading.value = true;

    try {
      const res = await api.post(`/chat/${targetChat.id}/send-message/`, {
        content: trimmed,
      });

      if (res.data?.user_message && res.data?.assistant_message) {
        const userMsgIndex = targetChat.messages.findIndex((m) => m.id === tempUserMsg.id);
        if (userMsgIndex !== -1) {
          targetChat.messages[userMsgIndex] = {
            id: String(res.data.user_message.id),
            role: res.data.user_message.role,
            content: res.data.user_message.content,
            createdAt: res.data.user_message.created_at,
          };
        }

        targetChat.messages.push({
          id: String(res.data.assistant_message.id),
          role: res.data.assistant_message.role,
          content: res.data.assistant_message.content,
          createdAt: res.data.assistant_message.created_at,
        });
      } else {
        const docNames = documentsStore.readyDocuments
          .map((doc) => doc.name)
          .join(", ");

        targetChat.messages.push({
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Based on your documents (${docNames}), here is a response to: "${trimmed}"`,
          createdAt: new Date().toISOString(),
        });
      }

      targetChat.updated_at = new Date().toISOString();
      saveToStorage();
    } catch (e: any) {
      console.warn("API send-message failed, using local fallback", e);
      const docNames = documentsStore.readyDocuments
        .map((doc) => doc.name)
        .join(", ");

      targetChat.messages.push({
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Based on your documents (${docNames}), here is a response to: "${trimmed}"`,
        createdAt: new Date().toISOString(),
      });
      targetChat.updated_at = new Date().toISOString();
      saveToStorage();
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
    fetchChats,
    createNewChat,
    selectChat,
    renameChat,
    deleteChat,
    sendMessage,
    clearMessages,
    saveToStorage,
  };
});
