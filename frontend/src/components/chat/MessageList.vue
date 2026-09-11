<script setup lang="ts">
import { nextTick, ref, watch } from "vue"
import { FileText, Sparkles, ArrowDown } from "@lucide/vue"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useChatStore } from "@/stores/chat"
import { useDocumentsStore } from "@/stores/documents"
import MessageBubble from "./MessageBubble.vue"

const chatStore = useChatStore()
const documentsStore = useDocumentsStore()

const scrollContainerRef = ref<HTMLElement | null>(null)
const scrollAnchor = ref<HTMLElement | null>(null)
const showScrollToBottom = ref(false)

function handleScroll() {
  if (!scrollContainerRef.value) return
  const el = scrollContainerRef.value
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollToBottom.value = distanceFromBottom > 80
}

async function scrollToBottom(smooth = true) {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: smooth ? "smooth" : "auto" })
  showScrollToBottom.value = false
}

watch(
  () => [chatStore.messages.length, chatStore.isLoading],
  async () => {
    await nextTick()
    if (!scrollContainerRef.value) {
      scrollToBottom(true)
      return
    }
    const el = scrollContainerRef.value
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    if (distanceFromBottom < 200 || !showScrollToBottom.value) {
      scrollToBottom(true)
    }
  },
  { deep: true }
)
</script>

<template>
  <div class="relative h-full w-full">
    <div
      ref="scrollContainerRef"
      class="h-full w-full overflow-y-auto"
      @scroll="handleScroll"
    >
      <div
        v-if="!chatStore.messages.length"
        class="flex h-full min-h-105 flex-col items-center justify-center gap-4 px-6 text-center"
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
    </div>

    <!-- Pinned Scroll to Bottom Button -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-2 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-2 scale-95"
    >
      <Button
        v-if="showScrollToBottom && chatStore.messages.length > 0"
        variant="outline"
        size="icon"
        class="absolute bottom-4 right-6 z-30 h-9 w-9 rounded-full bg-background/90 shadow-md border backdrop-blur-xs hover:bg-accent text-foreground cursor-pointer transition-all"
        title="Scroll to latest message"
        @click="scrollToBottom(true)"
      >
        <ArrowDown class="h-4 w-4 text-primary" />
        <span class="sr-only">Jump to latest message</span>
      </Button>
    </Transition>
  </div>
</template>
