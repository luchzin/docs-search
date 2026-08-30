<script setup lang="ts">
import { ref } from "vue"
import AppSidebar from "@/components/chat/AppSidebar.vue"
import ChatInput from "@/components/chat/ChatInput.vue"
import MessageList from "@/components/chat/MessageList.vue"
import { TooltipProvider } from "@/components/ui/tooltip"

const sidebarOpen = ref(true)
</script>

<template>
  <TooltipProvider>
    <div class="relative flex h-dvh overflow-hidden bg-background">
      <AppSidebar :open="sidebarOpen" @toggle="sidebarOpen = !sidebarOpen" />

      <main class="flex min-w-0 flex-1 flex-col">
        <header class="flex h-14 shrink-0 items-center border-b px-4">
          <h2 class="text-sm font-medium text-muted-foreground">
            RAG Document Chat
          </h2>
        </header>

        <div class="min-h-0 flex-1">
          <MessageList />
        </div>

        <ChatInput ></ChatInput>
      </main>
    </div>
  </TooltipProvider>
</template>
