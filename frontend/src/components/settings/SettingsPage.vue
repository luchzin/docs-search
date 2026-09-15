<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import {
  Sparkles,
  Bot,
  Brain,
  Zap,
  Check,
  Eye,
  EyeOff,
  Key,
  ShieldCheck,
  ArrowLeft,
  Settings,
  Cpu,
  Palette,
  Languages,
  Database,
  Sun,
  MoonStar,
  Trash2,
  Loader2,
  Save,
  LogOut,
  User,
  LogIn,
} from "lucide-vue-next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import AuthModal from "@/components/auth/AuthModal.vue";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDark } from "@vueuse/core";
import {
  useModelStore,
  type ModelOption,
  type ModelProvider,
} from "@/stores/model";
import { useChatStore } from "@/stores/chat";
import { useAuthStore } from "@/stores/auth";
import { setLanguage, type SupportedLocale } from "@/i18n";

const emit = defineEmits<{
  backToChat: [];
}>();

const { t, locale } = useI18n();
const modelStore = useModelStore();
const chatStore = useChatStore();
const authStore = useAuthStore();
const isDark = useDark();
const isAuthModalOpen = ref(false);

type SettingsTab = "account" | "model" | "appearance" | "language" | "data";
const activeTab = ref<SettingsTab>("model");

const localApiKey = ref(modelStore.currentApiKey);
const showApiKey = ref(false);

onMounted(() => {
  modelStore.fetchModelsFromBackend();
});

// Keep API key input updated when selected model changes
watch(
  () => modelStore.selectedModel.provider,
  (newProvider) => {
    localApiKey.value = modelStore.apiKeys[newProvider] || "";
  },
  { immediate: true }
);

function getProviderIcon(provider: ModelProvider) {
  switch (provider) {
    case "gemini":
      return Sparkles;
    case "openai":
      return Bot;
    case "claude":
      return Brain;
    case "deepseek":
      return Zap;
    default:
      return Cpu;
  }
}

function handleSelectModel(model: ModelOption) {
  modelStore.setModel(model.id);
  localApiKey.value = modelStore.apiKeys[model.provider] || "";
}

const isUploadingKey = ref(false);
const uploadStatusMessage = ref<string | null>(null);

function saveKey() {
  modelStore.setApiKey(modelStore.selectedModel.provider, localApiKey.value);
}

async function handleUploadApiKey() {
  saveKey();
  isUploadingKey.value = true;
  uploadStatusMessage.value = null;

  try {
    await uploadApiKey(modelStore.selectedModel.provider, localApiKey.value);
    uploadStatusMessage.value = t("settings.keySavedSuccess", { provider: modelStore.selectedModel.providerName });
  } catch (err: any) {
    console.error("API Key upload error:", err);
    uploadStatusMessage.value = `Error uploading key: ${err?.message || err}`;
  } finally {
    isUploadingKey.value = false;
  }
}

async function uploadApiKey(provider: ModelProvider, apiKey: string): Promise<void> {
  console.log(`[Custom API Key Upload] Provider: ${provider}, Key: ${apiKey ? 'Present' : 'Empty'}`);
}

function handleClearAllData() {
  if (confirm(t("settings.confirmClearStorage"))) {
    chatStore.clearMessages();
    localStorage.clear();
    location.reload();
  }
}

function changeLanguage(lang: SupportedLocale) {
  setLanguage(lang);
}
</script>

<template>
  <AuthModal v-model:open="isAuthModalOpen" />
  <div class="h-full overflow-y-auto bg-background p-4 sm:p-6 md:p-8">
    <div class="mx-auto max-w-5xl space-y-6">
      <!-- Top Header Bar -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Settings class="h-5 w-5" />
            </div>
            <h1 class="text-2xl font-bold tracking-tight text-foreground">
              {{ $t('settings.title') }}
            </h1>
          </div>
          <p class="text-sm text-muted-foreground">
            {{ $t('settings.subtitle') }}
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          class="shrink-0 gap-2 border-border shadow-2xs hover:bg-accent"
          @click="emit('backToChat')"
        >
          <ArrowLeft class="h-4 w-4" />
          <span>{{ $t('settings.backToChat') }}</span>
        </Button>
      </div>

      <!-- Settings Layout (Navigation Tabs + Main Content) -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
        <!-- Settings Sidebar / Tab Menu -->
        <nav class="flex md:flex-col gap-1.5 overflow-x-auto pb-2 md:pb-0 border-b md:border-b-0 shrink-0">
          <button
            type="button"
            :class="[
              'flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs font-medium transition-all text-left cursor-pointer whitespace-nowrap',
              activeTab === 'account'
                ? 'bg-primary/10 text-primary font-semibold shadow-2xs'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            ]"
            @click="activeTab = 'account'"
          >
            <User class="h-4 w-4 shrink-0" />
            <span>{{ $t('settings.accountTab') }}</span>
          </button>

          <button
            type="button"
            :class="[
              'flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs font-medium transition-all text-left cursor-pointer whitespace-nowrap',
              activeTab === 'model'
                ? 'bg-primary/10 text-primary font-semibold shadow-2xs'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            ]"
            @click="activeTab = 'model'"
          >
            <Cpu class="h-4 w-4 shrink-0" />
            <span>{{ $t('settings.modelTab') }}</span>
          </button>

          <button
            type="button"
            :class="[
              'flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs font-medium transition-all text-left cursor-pointer whitespace-nowrap',
              activeTab === 'appearance'
                ? 'bg-primary/10 text-primary font-semibold shadow-2xs'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            ]"
            @click="activeTab = 'appearance'"
          >
            <Palette class="h-4 w-4 shrink-0" />
            <span>{{ $t('settings.appearanceTab') }}</span>
          </button>

          <button
            type="button"
            :class="[
              'flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs font-medium transition-all text-left cursor-pointer whitespace-nowrap',
              activeTab === 'language'
                ? 'bg-primary/10 text-primary font-semibold shadow-2xs'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            ]"
            @click="activeTab = 'language'"
          >
            <Languages class="h-4 w-4 shrink-0" />
            <span>{{ $t('settings.languageTab') }}</span>
          </button>

          <button
            type="button"
            :class="[
              'flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs font-medium transition-all text-left cursor-pointer whitespace-nowrap',
              activeTab === 'data'
                ? 'bg-primary/10 text-primary font-semibold shadow-2xs'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            ]"
            @click="activeTab = 'data'"
          >
            <Database class="h-4 w-4 shrink-0" />
            <span>{{ $t('settings.dataTab') }}</span>
          </button>
        </nav>

        <!-- Main Content Area -->
        <div class="md:col-span-3 space-y-6">
          <!-- TAB: Account & Session -->
          <div v-if="activeTab === 'account'" class="space-y-6">
            <Card class="border shadow-2xs">
              <CardHeader class="pb-3 border-b">
                <div class="flex items-center gap-2">
                  <User class="h-5 w-5 text-primary" />
                  <CardTitle class="text-lg">{{ $t('settings.userAccount') }}</CardTitle>
                </div>
                <CardDescription class="text-xs">
                  {{ $t('settings.manageAccountSub') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="pt-4 space-y-4">
                <template v-if="authStore.isAuthenticated && authStore.user">
                  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-xl border p-4 gap-4">
                    <div class="flex items-center gap-3">
                      <Avatar class="h-10 w-10">
                        <AvatarFallback class="text-sm uppercase bg-primary/10 text-primary font-bold">
                          {{ (authStore.user.username || authStore.user.email || "U").slice(0, 2) }}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p class="text-sm font-semibold text-foreground">
                          {{ authStore.user.username || authStore.user.email }}
                        </p>
                        <p class="text-xs text-muted-foreground">
                          {{ authStore.user.email }}
                        </p>
                      </div>
                    </div>

                    <Button
                      variant="destructive"
                      size="sm"
                      class="gap-2 shrink-0 font-semibold"
                      @click="authStore.logout()"
                    >
                      <LogOut class="h-4 w-4" />
                      <span>{{ $t('settings.logoutBtn') }}</span>
                    </Button>
                  </div>
                </template>
                <template v-else>
                  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-xl border p-4 gap-4">
                    <div class="space-y-0.5">
                      <p class="text-sm font-semibold text-foreground">
                        {{ $t('settings.notLoggedIn') }}
                      </p>
                      <p class="text-xs text-muted-foreground">
                        {{ $t('settings.signInSyncNotice') }}
                      </p>
                    </div>
                    <Button
                      variant="default"
                      size="sm"
                      class="gap-2 shrink-0 font-semibold"
                      @click="isAuthModalOpen = true"
                    >
                      <LogIn class="h-4 w-4" />
                      <span>{{ $t('header.signInRegister') }}</span>
                    </Button>
                  </div>
                </template>
              </CardContent>
            </Card>
          </div>

          <!-- TAB 1: AI Model Selection & API Key Configuration -->
          <div v-else-if="activeTab === 'model'" class="space-y-6">
            <!-- Model Selection Cards Grid -->
            <Card class="border shadow-2xs">
              <CardHeader class="pb-3 border-b">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <Sparkles class="h-5 w-5 text-primary" />
                    <CardTitle class="text-lg">{{ $t('settings.selectModel') }}</CardTitle>
                  </div>
                  <Badge variant="outline" class="text-xs font-medium">
                    {{ $t('settings.active') }}: {{ modelStore.selectedModel.name }}
                  </Badge>
                </div>
                <CardDescription class="text-xs mt-1">
                  {{ $t('settings.modelSub') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="pt-4 space-y-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div
                    v-for="model in modelStore.modelsList"
                    :key="model.id"
                    :class="[
                      'group relative flex items-start justify-between rounded-xl border p-3.5 cursor-pointer transition-all select-none',
                      modelStore.selectedModelId === model.id
                        ? 'border-primary bg-primary/5 shadow-xs ring-1 ring-primary/30'
                        : 'border-border hover:border-muted-foreground/40 hover:bg-muted/30'
                    ]"
                    @click="handleSelectModel(model)"
                  >
                    <div class="flex items-start gap-3 min-w-0 pr-2">
                      <div
                        :class="[
                          'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border shadow-2xs mt-0.5',
                          modelStore.selectedModelId === model.id
                            ? 'bg-primary text-primary-foreground border-primary'
                            : 'bg-muted text-muted-foreground border-border'
                        ]"
                      >
                        <component :is="getProviderIcon(model.provider)" class="h-4 w-4" />
                      </div>

                      <div class="min-w-0 space-y-1">
                        <div class="flex items-center gap-2 flex-wrap">
                          <span class="text-xs font-semibold text-foreground">
                            {{ model.name }}
                          </span>
                          <Badge
                            v-if="model.isDefault"
                            variant="secondary"
                            class="text-[9px] py-0 px-1 font-bold uppercase tracking-wider"
                          >
                            {{ $t('settings.defaultTag') }}
                          </Badge>
                        </div>
                        <p class="text-[11px] text-muted-foreground line-clamp-2 leading-tight">
                          {{ model.description }}
                        </p>
                      </div>
                    </div>

                    <div
                      v-if="modelStore.selectedModelId === model.id"
                      class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground"
                    >
                      <Check class="h-3 w-3" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Gemini Default Banner (No API key form required) -->
            <div v-if="modelStore.isDefaultGemini" class="space-y-4">
              <Card class="border border-primary/20 bg-primary/5 shadow-2xs">
                <CardHeader class="pb-3">
                  <div class="flex items-center gap-2.5">
                    <Sparkles class="h-5 w-5 text-primary shrink-0" />
                    <CardTitle class="text-base font-semibold text-foreground">
                      {{ $t('settings.defaultGeminiNotice') }}
                    </CardTitle>
                  </div>
                  <CardDescription class="text-xs mt-1.5 leading-relaxed text-muted-foreground">
                    {{ $t('settings.defaultGeminiSub') }}
                  </CardDescription>
                </CardHeader>
                <CardContent class="pt-0 pb-4">
                  <div class="flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-3 py-2 rounded-lg border border-emerald-500/20">
                    <ShieldCheck class="h-4 w-4 shrink-0" />
                    <span>{{ $t('settings.systemIntegrationNotice') }}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Focused API Key Card ONLY for non-default models that require user API key -->
            <div v-else-if="modelStore.requiresApiKey" class="space-y-4">
              <Card class="border shadow-2xs">
                <CardHeader class="pb-3 border-b">
                  <div class="flex items-center gap-2">
                    <Key class="h-5 w-5 text-primary" />
                    <CardTitle class="text-lg">
                      {{ $t('settings.apiKeyFor', { provider: modelStore.selectedModel.providerName }) }}
                    </CardTitle>
                  </div>
                  <CardDescription class="text-xs mt-1">
                    {{ $t('settings.apiKeySub', { model: modelStore.selectedModel.name }) }}
                  </CardDescription>
                </CardHeader>
                <CardContent class="pt-4">
                  <div class="rounded-xl border border-border bg-muted/20 p-4 space-y-3">
                    <div class="flex items-center justify-between">
                      <Label for="active-api-key" class="text-xs font-semibold flex items-center gap-1.5">
                        <component :is="getProviderIcon(modelStore.selectedModel.provider)" class="h-4 w-4 text-primary" />
                        <span>{{ $t('settings.apiKeyHeader', { provider: modelStore.selectedModel.providerName }) }}</span>
                      </Label>
                      <span v-if="modelStore.currentApiKey" class="text-xs text-emerald-600 font-medium flex items-center gap-1">
                        <ShieldCheck class="h-3.5 w-3.5" /> {{ $t('settings.keySet') }}
                      </span>
                      <Badge v-else variant="outline" class="text-[10px] text-muted-foreground font-normal">
                        {{ $t('settings.requiredForModel', { model: modelStore.selectedModel.name }) }}
                      </Badge>
                    </div>

                    <div class="relative">
                      <Input
                        id="active-api-key"
                        v-model="localApiKey"
                        :type="showApiKey ? 'text' : 'password'"
                        :placeholder="$t('settings.enterKeyPlaceholder', { provider: modelStore.selectedModel.providerName })"
                        class="pr-10 text-xs h-9.5"
                        @blur="saveKey"
                        @keyup.enter="saveKey"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        class="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-foreground"
                        @click="showApiKey = !showApiKey"
                      >
                        <EyeOff v-if="showApiKey" class="h-3.5 w-3.5" />
                        <Eye v-else class="h-3.5 w-3.5" />
                      </Button>
                    </div>

                    <div class="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span class="flex items-center gap-1">
                        <ShieldCheck class="h-3 w-3 text-emerald-500" />
                        {{ $t('settings.apiKeySavedLocally') }}
                      </span>
                      <span v-if="modelStore.currentApiKey" class="text-emerald-600 font-medium">
                        {{ $t('settings.activeKeySaved') }}
                      </span>
                    </div>

                    <!-- Submit API Key Action Button -->
                    <div class="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-t">
                      <p v-if="uploadStatusMessage" class="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                        {{ uploadStatusMessage }}
                      </p>
                      <p v-else class="text-[11px] text-muted-foreground">
                        {{ $t('settings.submitNotice', { provider: modelStore.selectedModel.providerName }) }}
                      </p>
                      <Button
                        type="button"
                        size="sm"
                        class="gap-2 shrink-0 h-9 text-xs font-semibold px-4"
                        :disabled="isUploadingKey"
                        @click="handleUploadApiKey"
                      >
                        <Loader2 v-if="isUploadingKey" class="h-3.5 w-3.5 animate-spin" />
                        <Save v-else class="h-3.5 w-3.5" />
                        <span>{{ $t('settings.saveApiKeyBtn') }}</span>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <!-- TAB 2: Appearance -->
          <div v-else-if="activeTab === 'appearance'" class="space-y-6">
            <Card class="border shadow-2xs">
              <CardHeader class="pb-3 border-b">
                <div class="flex items-center gap-2">
                  <Palette class="h-5 w-5 text-primary" />
                  <CardTitle class="text-lg">{{ $t('settings.appearanceTab') }}</CardTitle>
                </div>
                <CardDescription class="text-xs">
                  {{ $t('settings.colorThemeSub') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="pt-4 space-y-4">
                <div class="flex items-center justify-between rounded-xl border p-4">
                  <div class="space-y-0.5">
                    <span class="text-sm font-semibold">{{ $t('settings.colorTheme') }}</span>
                    <p class="text-xs text-muted-foreground">
                      {{ $t('settings.colorThemeSub') }}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" class="gap-2" @click="isDark = !isDark">
                    <Sun v-if="isDark" class="h-4 w-4" />
                    <MoonStar v-else class="h-4 w-4" />
                    <span>{{ isDark ? $t('settings.darkMode') : $t('settings.lightMode') }}</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- TAB 3: Language -->
          <div v-else-if="activeTab === 'language'" class="space-y-6">
            <Card class="border shadow-2xs">
              <CardHeader class="pb-3 border-b">
                <div class="flex items-center gap-2">
                  <Languages class="h-5 w-5 text-primary" />
                  <CardTitle class="text-lg">{{ $t('settings.selectLanguage') }}</CardTitle>
                </div>
                <CardDescription class="text-xs">
                  {{ $t('settings.selectLanguageSub') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="pt-4 space-y-3">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <!-- English option -->
                  <div
                    :class="[
                      'flex items-center justify-between rounded-xl border p-4 cursor-pointer transition-all select-none',
                      locale === 'en'
                        ? 'border-primary bg-primary/5 shadow-xs ring-1 ring-primary/30'
                        : 'border-border hover:border-muted-foreground/40 hover:bg-muted/30'
                    ]"
                    @click="changeLanguage('en')"
                  >
                    <div class="flex items-center gap-3">
                      <span class="text-lg">🇬🇧</span>
                      <div>
                        <p class="text-sm font-semibold text-foreground">English</p>
                        <p class="text-xs text-muted-foreground">English (អង់គ្លេស)</p>
                      </div>
                    </div>
                    <div
                      v-if="locale === 'en'"
                      class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground"
                    >
                      <Check class="h-3 w-3" />
                    </div>
                  </div>

                  <!-- Khmer option -->
                  <div
                    :class="[
                      'flex items-center justify-between rounded-xl border p-4 cursor-pointer transition-all select-none',
                      locale === 'km'
                        ? 'border-primary bg-primary/5 shadow-xs ring-1 ring-primary/30'
                        : 'border-border hover:border-muted-foreground/40 hover:bg-muted/30'
                    ]"
                    @click="changeLanguage('km')"
                  >
                    <div class="flex items-center gap-3">
                      <span class="text-lg">🇰🇭</span>
                      <div>
                        <p class="text-sm font-semibold text-foreground">ភាសាខ្មែរ</p>
                        <p class="text-xs text-muted-foreground">Khmer (ភាសាខ្មែរ)</p>
                      </div>
                    </div>
                    <div
                      v-if="locale === 'km'"
                      class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground"
                    >
                      <Check class="h-3 w-3" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- TAB 4: Data & Storage -->
          <div v-else-if="activeTab === 'data'" class="space-y-6">
            <Card class="border shadow-2xs border-destructive/20">
              <CardHeader class="pb-3 border-b border-destructive/10">
                <div class="flex items-center gap-2">
                  <Database class="h-5 w-5 text-destructive" />
                  <CardTitle class="text-lg text-destructive">{{ $t('settings.dataTab') }}</CardTitle>
                </div>
                <CardDescription class="text-xs">
                  {{ $t('settings.clearStorageSub') }}
                </CardDescription>
              </CardHeader>
              <CardContent class="pt-4 space-y-4">
                <div class="flex items-center justify-between rounded-xl border border-destructive/20 bg-destructive/5 p-4">
                  <div class="space-y-0.5">
                    <span class="text-sm font-semibold text-destructive">{{ $t('settings.clearStorage') }}</span>
                    <p class="text-xs text-muted-foreground">
                      {{ $t('settings.clearStorageSub') }}
                    </p>
                  </div>
                  <Button variant="destructive" size="sm" class="gap-1.5" @click="handleClearAllData">
                    <Trash2 class="h-4 w-4" />
                    <span>{{ $t('settings.clearStorageBtn') }}</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
