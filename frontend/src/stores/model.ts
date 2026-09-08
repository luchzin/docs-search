import { defineStore } from "pinia";
import { ref, computed } from "vue";

export type ModelProvider = "gemini" | "openai" | "claude" | "deepseek";

export interface ModelOption {
  id: string;
  name: string;
  provider: ModelProvider;
  providerName: string;
  description: string;
  isDefault?: boolean;
}

export const AVAILABLE_MODELS: ModelOption[] = [
  {
    id: "gemini-2.0-flash",
    name: "Gemini 2.0 Flash",
    provider: "gemini",
    providerName: "Google Gemini",
    description: "Fast, highly performant model by Google (Default)",
    isDefault: true,
  },
  {
    id: "gemini-1.5-pro",
    name: "Gemini 1.5 Pro",
    provider: "gemini",
    providerName: "Google Gemini",
    description: "Advanced reasoning with high quality responses",
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "openai",
    providerName: "OpenAI ChatGPT",
    description: "Flagship intelligence model for multimodal tasks",
  },
  {
    id: "gpt-4o-mini",
    name: "GPT-4o Mini",
    provider: "openai",
    providerName: "OpenAI ChatGPT",
    description: "Lightweight and efficient OpenAI model",
  },
  {
    id: "claude-3-5-sonnet",
    name: "Claude 3.5 Sonnet",
    provider: "claude",
    providerName: "Anthropic Claude",
    description: "State-of-the-art reasoning and coding performance",
  },
  {
    id: "deepseek-chat",
    name: "DeepSeek V3",
    provider: "deepseek",
    providerName: "DeepSeek AI",
    description: "High efficiency open-weights baseline model",
  },
];

const STORAGE_KEY = "doc_search_model_settings";

interface ModelStorageData {
  selectedModelId: string;
  apiKeys: Record<ModelProvider, string>;
}

export const useModelStore = defineStore("model", () => {
  const selectedModelId = ref<string>("gemini-2.0-flash");
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
      AVAILABLE_MODELS.find((m) => m.id === selectedModelId.value) ||
      AVAILABLE_MODELS[0]
    );
  });

  const currentApiKey = computed<string>(() => {
    const provider = selectedModel.value.provider;
    return apiKeys.value[provider] || "";
  });

  function setModel(modelId: string) {
    if (AVAILABLE_MODELS.some((m) => m.id === modelId)) {
      selectedModelId.value = modelId;
      saveToStorage();
    }
  }

  function setApiKey(provider: ModelProvider, key: string) {
    apiKeys.value[provider] = key.trim();
    saveToStorage();
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
    apiKeys,
    currentApiKey,
    AVAILABLE_MODELS,
    setModel,
    setApiKey,
  };
});
