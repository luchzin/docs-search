<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useDark } from "@vueuse/core";
import AppSidebar from "@/components/chat/AppSidebar.vue";
import ChatInput from "@/components/chat/ChatInput.vue";
import MessageList from "@/components/chat/MessageList.vue";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MoonStar, Sun, PanelLeftOpen, PanelLeftClose, LogOut, LogIn } from "@lucide/vue";
import AuthModal from "@/components/auth/AuthModal.vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const sidebarOpen = ref(
  typeof window !== "undefined" ? window.innerWidth >= 768 : true,
);
const isAuthModalOpen = ref(false);
const isDark = useDark();

onMounted(async () => {
  if (window.innerWidth < 768) {
    sidebarOpen.value = false;
  }
  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser();
  }
  if (!authStore.isAuthenticated) {
    isAuthModalOpen.value = true;
  }
});
</script>

<template>
  <TooltipProvider>
    <div class="relative flex h-dvh overflow-hidden bg-background">
      <AppSidebar :open="sidebarOpen" @toggle="sidebarOpen = !sidebarOpen" />

      <main class="flex min-w-0 flex-1 flex-col">
        <header
          class="flex h-14 shrink-0 items-center justify-between border-b px-3 sm:px-4"
        >
          <div class="flex items-center gap-2">
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
            <h2 class="text-sm font-semibold text-foreground truncate">
              RAG Document Chat
            </h2>
          </div>

          <div class="flex items-center space-x-2 sm:space-x-4">
            <AuthModal v-model:open="isAuthModalOpen" />

            <!-- User Auth Status Display -->
            <template v-if="authStore.isAuthenticated && authStore.user">
              <div class="flex items-center gap-2">
                <Avatar class="h-7 w-7">
                  <AvatarFallback class="text-xs uppercase bg-primary/10 text-primary font-medium">
                    {{ (authStore.user.username || authStore.user.email || "U").slice(0, 2) }}
                  </AvatarFallback>
                </Avatar>
                <span class="text-xs font-medium text-muted-foreground hidden md:inline truncate max-w-[120px]">
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
                variant="outline"
                size="sm"
                class="h-8 text-xs gap-1.5"
                @click="isAuthModalOpen = true"
              >
                <LogIn class="h-3.5 w-3.5" />
                Sign In
              </Button>
            </template>

            <!-- Theme Toggle -->
            <Button variant="ghost" size="icon" @click="isDark = !isDark">
              <Sun v-if="isDark" class="h-4 w-4" />
              <MoonStar v-else class="h-4 w-4" />
              <span class="sr-only">Toggle dark mode</span>
            </Button>

            <!-- GitHub Link with Custom SVG -->
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

        <div class="min-h-0 flex-1">
          <MessageList />
        </div>

        <ChatInput />
      </main>
    </div>
  </TooltipProvider>
</template>
