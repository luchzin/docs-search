<script setup lang="ts">
import { nextTick, ref, watch } from "vue"
import { FileText, Sparkles } from "@lucide/vue"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { useChatStore } from "@/stores/chat"
import { useDocumentsStore } from "@/stores/documents"
import MessageBubble from "./MessageBubble.vue"

const chatStore = useChatStore()
const documentsStore = useDocumentsStore()
const scrollAnchor = ref<HTMLElement | null>(null)

watch(
  () => [chatStore.messages.length, chatStore.isLoading],
  async () => {
    await nextTick()
    scrollAnchor.value?.scrollIntoView({ behavior: "smooth" })
  },
)
</script>

<template>
  <ScrollArea class="h-full">
    <div
      v-if="!chatStore.messages.length"
      class="flex h-full min-h-[420px] flex-col items-center justify-center gap-4 px-6 text-center"
    >
      <div class="flex size-12 items-center justify-center rounded-full bg-primary/10">
        <Sparkles class="size-6 text-primary" />
      </div>
      <div class="max-w-md space-y-2">
        <h2 class="text-xl font-semibold">Ask questions about your documents</h2>
        <p class="text-sm text-muted-foreground">
          Upload PDF support documents in the sidebar, then ask anything related to their content.
        </p>
      </div>
      <div
        v-if="!documentsStore.hasDocuments"
        class="flex items-center gap-2 rounded-lg border border-dashed px-4 py-3 text-sm text-muted-foreground"
      >
        <FileText class="size-4" />
        Start by uploading a PDF in the sidebar
      </div>
    </div>

    <template v-else>
      <MessageBubble
        v-for="message in chatStore.messages"
        :key="message.id"
        :message="message"
      />

      <div
        v-if="chatStore.isLoading"
        class="flex gap-3 bg-muted/30 px-3 sm:px-4 py-4 sm:py-5"
      >
        <Skeleton class="size-8 shrink-0 rounded-full" />
        <div class="flex-1 space-y-2">
          <Skeleton class="h-4 w-24" />
          <Skeleton class="h-4 w-full max-w-lg" />
          <Skeleton class="h-4 w-3/4 max-w-md" />
        </div>
      </div>
    </template>

    <div ref="scrollAnchor" class="h-px" />
  </ScrollArea>
</template>
