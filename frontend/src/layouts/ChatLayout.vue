<script setup lang="ts">
import { ref, computed, watchEffect, onMounted, watch } from "vue";
import { useDark } from "@vueuse/core";
import AppSidebar from "@/components/chat/AppSidebar.vue";
import ChatInput from "@/components/chat/ChatInput.vue";
import MessageList from "@/components/chat/MessageList.vue";
import SettingsPage from "@/components/settings/SettingsPage.vue";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  MoonStar,
  Sun,
  PanelLeftOpen,
  PanelLeftClose,
  LogOut,
  LogIn,
  Download,
  Lock,
} from "@lucide/vue";
import AuthModal from "@/components/auth/AuthModal.vue";
import { useAuthStore } from "../stores/auth";
import { useChatStore } from "../stores/chat";

const authStore = useAuthStore();
const chatStore = useChatStore();

const activeView = ref<"chat" | "settings">("chat");
const sidebarOpen = ref(
  typeof window !== "undefined" ? window.innerWidth >= 768 : true
);
const isAuthModalOpen = ref(false);
const isDark = useDark();

const pageTitle = computed(() => {
  if (!authStore.isAuthenticated) {
    return "Sign In - Doc Search";
  }
  if (activeView.value === "settings") {
    return "Settings & Configuration - Doc Search";
  }
  if (chatStore.activeChat?.title) {
    return `${chatStore.activeChat.title} - Doc Search`;
  }
  return "RAG Document Chat - Doc Search";
});

watchEffect(() => {
  document.title = pageTitle.value;
});

onMounted(async () => {
  if (window.innerWidth < 768) {
    sidebarOpen.value = false;
  }
  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser();
  }
  if (authStore.isAuthenticated) {
    await chatStore.fetchChats();
  } else {
    isAuthModalOpen.value = true;
  }
});

watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      chatStore.fetchChats();
    } else {
      isAuthModalOpen.value = true;
    }
  }
);

function download() {
  if ((navigator as any).userAgentData?.getHighEntropyValues) {
    (navigator as any).userAgentData
      .getHighEntropyValues(["platform"])
      .then((ua: { platform: string }) => {
        const isWindowsHighEntropy = ua.platform === "Windows";
        console.log("Is Windows:", isWindowsHighEntropy);
      });
  }
}
</script>

<template>
  <TooltipProvider>
    <div class="relative flex h-dvh overflow-hidden bg-background">
      <AppSidebar
        :open="sidebarOpen"
        :current-view="activeView"
        @toggle="sidebarOpen = !sidebarOpen"
        @open-settings="activeView = 'settings'"
        @open-chat="activeView = 'chat'"
      />

      <main class="flex min-w-0 flex-1 flex-col">
        <!-- Header -->
        <header
          class="flex h-14 shrink-0 items-center justify-between border-b px-3 sm:px-4"
        >
          <div class="flex items-center gap-2 min-w-0">
            <Button
              variant="ghost"
              size="icon-sm"
              class="shrink-0"
              @click="sidebarOpen = !sidebarOpen"
            >
              <PanelLeftClose v-if="sidebarOpen" class="size-4" />
              <PanelLeftOpen v-else class="size-4" />
              <span class="sr-only">Toggle sidebar</span>
            </Button>
            <h2
              class="text-sm font-semibold text-foreground truncate max-w-45 sm:max-w-xs md:max-w-sm"
            >
              {{
                !authStore.isAuthenticated
                  ? "Authentication Required"
                  : activeView === "settings"
                  ? "Settings & Configuration"
                  : chatStore.activeChat?.title || "RAG Document Chat"
              }}
            </h2>
          </div>

          <div class="flex items-center space-x-2 sm:space-x-3">
            <AuthModal v-model:open="isAuthModalOpen" />

            <!-- User Auth Status Display -->
            <template v-if="authStore.isAuthenticated && authStore.user">
              <div class="flex items-center gap-2">
                <Avatar class="h-7 w-7">
                  <AvatarFallback
                    class="text-xs uppercase bg-primary/10 text-primary font-medium"
                  >
                    {{
                      (
                        authStore.user.username ||
                        authStore.user.email ||
                        "U"
                      ).slice(0, 2)
                    }}
                  </AvatarFallback>
                </Avatar>
                <span
                  class="text-xs font-medium text-muted-foreground hidden md:inline truncate max-w-30"
                >
                  {{ authStore.user.username || authStore.user.email }}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  class="h-8 text-xs text-muted-foreground hover:text-foreground gap-1 px-2"
                  @click="authStore.logout()"
                  title="Sign Out"
                >
                  <LogOut class="h-3.5 w-3.5" />
                  <span class="hidden sm:inline">Logout</span>
                </Button>
              </div>
            </template>
            <template v-else>
              <Button
                variant="default"
                size="sm"
                class="h-8 text-xs gap-1.5 font-semibold"
                @click="isAuthModalOpen = true"
              >
                <LogIn class="h-3.5 w-3.5" />
                Sign In / Register
              </Button>
            </template>

            <!-- Theme Toggle -->
            <Button
              variant="ghost"
              size="icon"
              class="h-8 w-8 px-0"
              @click="isDark = !isDark"
            >
              <Sun v-if="isDark" class="h-4 w-4" />
              <MoonStar v-else class="h-4 w-4" />
              <span class="sr-only">Toggle dark mode</span>
            </Button>

            <!-- Download button -->
            <Button
              variant="ghost"
              size="icon"
              class="h-8 w-8 px-0"
              @click="download"
              title="Download Application"
            >
              <Download class="h-4 w-4" />
            </Button>

            <!-- GitHub Link -->
            <Button variant="ghost" size="icon" as-child>
              <a
                href="https://github.com/luchzin/docs-search"
                target="_blank"
                rel="noreferrer"
                aria-label="GitHub Repository"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  fill="currentColor"
                  class="h-5 w-5"
                  viewBox="0 0 16 16"
                >
                  <path
                    d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"
                  />
                </svg>
              </a>
            </Button>
          </div>
        </header>

        <!-- Main Body: Unauthenticated Guard OR Settings View OR Chat View -->
        <template v-if="!authStore.isAuthenticated">
          <div class="flex flex-1 flex-col items-center justify-center p-6 text-center bg-muted/10">
            <div class="mx-auto max-w-md space-y-4 rounded-2xl border bg-card p-8 shadow-md">
              <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
                <Lock class="h-7 w-7" />
              </div>
              <div class="space-y-1.5">
                <h3 class="text-xl font-bold tracking-tight text-foreground">
                  Sign In Required
                </h3>
                <p class="text-xs text-muted-foreground leading-relaxed">
                  You must be logged in to view chat messages, upload documents, or configure AI model settings.
                </p>
              </div>
              <Button
                size="default"
                class="w-full font-semibold gap-2 mt-2"
                @click="isAuthModalOpen = true"
              >
                <LogIn class="h-4 w-4" />
                <span>Sign In / Create Account</span>
              </Button>
            </div>
          </div>
        </template>
        <template v-else-if="activeView === 'settings'">
          <SettingsPage @back-to-chat="activeView = 'chat'" />
        </template>
        <template v-else>
          <div class="min-h-0 flex-1">
            <MessageList />
          </div>
          <ChatInput />
        </template>
      </main>
    </div>
  </TooltipProvider>
</template>
