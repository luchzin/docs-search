import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/lib/utils";

export type ModelProvider = "gemini" | "openai" | "claude" | "deepseek";

export interface ModelOption {
  id: string;
  name: string;
  provider: ModelProvider;
  providerName: string;
  description: string;
  isDefault?: boolean;
  requiresApiKey?: boolean;
}

export const AVAILABLE_MODELS: ModelOption[] = [
  {
    id: "gemini-3.6-flash",
    name: "Gemini 3.6 Flash",
    provider: "gemini",
    providerName: "Google Gemini",
    description: "Fast, highly performant model by Google (Default, Built-in AI)",
    isDefault: true,
    requiresApiKey: false,
  },
  {
    id: "gemini-1.5-pro",
    name: "Gemini 1.5 Pro",
    provider: "gemini",
    providerName: "Google Gemini",
    description: "Advanced reasoning with high quality responses",
    isDefault: false,
    requiresApiKey: false,
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "openai",
    providerName: "OpenAI ChatGPT",
    description: "Flagship intelligence model for multimodal tasks",
    requiresApiKey: true,
  },
  {
    id: "gpt-4o-mini",
    name: "GPT-4o Mini",
    provider: "openai",
    providerName: "OpenAI ChatGPT",
    description: "Lightweight and efficient OpenAI model",
    requiresApiKey: true,
  },
  {
    id: "claude-3-5-sonnet",
    name: "Claude 3.5 Sonnet",
    provider: "claude",
    providerName: "Anthropic Claude",
    description: "State-of-the-art reasoning and coding performance",
    requiresApiKey: true,
  },
  {
    id: "deepseek-chat",
    name: "DeepSeek V3",
    provider: "deepseek",
    providerName: "DeepSeek AI",
    description: "High efficiency open-weights baseline model",
    requiresApiKey: true,
  },
];

const STORAGE_KEY = "doc_search_model_settings";

interface ModelStorageData {
  selectedModelId: string;
  apiKeys: Record<ModelProvider, string>;
}

export const useModelStore = defineStore("model", () => {
  const selectedModelId = ref<string>("gemini-3.6-flash");
  const modelsList = ref<ModelOption[]>(AVAILABLE_MODELS);
  const apiKeys = ref<Record<ModelProvider, string>>({
    gemini: "",
    openai: "",
    claude: "",
    deepseek: "",
  });

  // Load initial state from storage
  loadFromStorage();

  const selectedModel = computed<ModelOption>(() => {
    return (
      modelsList.value.find((m) => m.id === selectedModelId.value) ||
      modelsList.value[0]
    );
  });

  // Gemini (default AI) does not require user API form
  const isDefaultGemini = computed<boolean>(() => {
    return selectedModel.value.provider === "gemini";
  });

  const requiresApiKey = computed<boolean>(() => {
    return !isDefaultGemini.value && (selectedModel.value.requiresApiKey ?? true);
  });

  const currentApiKey = computed<string>(() => {
    const provider = selectedModel.value.provider;
    return apiKeys.value[provider] || "";
  });

  function setModel(modelId: string) {
    if (modelsList.value.some((m) => m.id === modelId)) {
      selectedModelId.value = modelId;
      saveToStorage();
      syncWithBackend();
    }
  }

  function setApiKey(provider: ModelProvider, key: string) {
    apiKeys.value[provider] = key.trim();
    saveToStorage();
    syncWithBackend();
  }

  async function syncWithBackend() {
    try {
      await api.post("/ai-config/", {
        selected_model_id: selectedModelId.value,
        api_keys: apiKeys.value,
      });
    } catch (e) {
      // Ignore if offline
    }
  }

  async function fetchModelsFromBackend() {
    try {
      const res = await api.get<any[]>("/models/");
      if (Array.isArray(res.data) && res.data.length > 0) {
        modelsList.value = res.data.map((m: any) => ({
          id: m.id || m.model_id,
          name: m.name,
          provider: m.provider as ModelProvider,
          providerName: m.provider_name,
          description: m.description,
          isDefault: Boolean(m.is_default),
          requiresApiKey: Boolean(m.requires_api_key),
        }));
      }
    } catch (e) {
      // Use fallback AVAILABLE_MODELS
    }
  }

  function saveToStorage() {
    try {
      const data: ModelStorageData = {
        selectedModelId: selectedModelId.value,
        apiKeys: apiKeys.value,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      console.error("Failed to save model settings to storage", e);
    }
  }

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data: ModelStorageData = JSON.parse(raw);
        if (
          data.selectedModelId &&
          AVAILABLE_MODELS.some((m) => m.id === data.selectedModelId)
        ) {
          selectedModelId.value = data.selectedModelId;
        }
        if (data.apiKeys) {
          apiKeys.value = {
            ...apiKeys.value,
            ...data.apiKeys,
          };
        }
      }
    } catch (e) {
      console.error("Failed to load model settings from storage", e);
    }
  }

  return {
    selectedModelId,
    selectedModel,
    isDefaultGemini,
    requiresApiKey,
    apiKeys,
    currentApiKey,
    modelsList,
    AVAILABLE_MODELS,
    setModel,
    setApiKey,
    fetchModelsFromBackend,
  };
});
