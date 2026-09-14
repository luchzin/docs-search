<script setup lang="ts">
import { nextTick, ref, watch } from "vue"
import { FileText, Sparkles, ArrowDown, Loader2 } from "lucide-vue-next"
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
const isFetchingOlder = ref(false)

const lastMessageId = ref<string | null>(null)

async function handleScroll() {
  if (!scrollContainerRef.value) return
  const el = scrollContainerRef.value

  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollToBottom.value = distanceFromBottom > 80

  // Upward infinite scroll trigger when scrolling near top
  if (
    el.scrollTop < 50 &&
    chatStore.activeChatId &&
    chatStore.activeChat?.hasMoreMessages &&
    !chatStore.activeChat?.isLoadingOlder &&
    !isFetchingOlder.value
  ) {
    isFetchingOlder.value = true
    const oldScrollHeight = el.scrollHeight
    await chatStore.fetchMessagesForChat(chatStore.activeChatId, { reset: false })
    await nextTick()
    if (scrollContainerRef.value) {
      const newScrollHeight = scrollContainerRef.value.scrollHeight
      scrollContainerRef.value.scrollTop = newScrollHeight - oldScrollHeight
    }
    isFetchingOlder.value = false
  }
}

async function scrollToBottom(smooth = true) {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: smooth ? "smooth" : "auto" })
  showScrollToBottom.value = false
}

watch(
  () => chatStore.activeChatId,
  async (newId) => {
    if (newId) {
      await nextTick()
      scrollToBottom(false)
    }
  },
  { immediate: true }
)

watch(
  () => chatStore.messages,
  async (newMessages) => {
    if (!newMessages.length) {
      lastMessageId.value = null
      return
    }
    const newLast = newMessages[newMessages.length - 1]?.id

    // Auto scroll down if a new message was appended to bottom
    if (newLast && newLast !== lastMessageId.value) {
      lastMessageId.value = newLast
      await nextTick()
      if (!scrollContainerRef.value) {
        scrollToBottom(true)
        return
      }
      const el = scrollContainerRef.value
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      if (distanceFromBottom < 250 || !showScrollToBottom.value) {
        scrollToBottom(true)
      }
    }
  },
  { deep: true }
)

watch(
  () => chatStore.isLoading,
  async (loading) => {
    if (loading) {
      await nextTick()
      scrollToBottom(true)
    }
  }
)
</script>

<template>
  <div class="relative h-full w-full">
    <div
      ref="scrollContainerRef"
      class="h-full w-full overflow-y-auto"
      @scroll="handleScroll"
    >
      <!-- Top Loader when loading older messages -->
      <div
        v-if="chatStore.activeChat?.isLoadingOlder"
        class="flex justify-center py-3"
      >
        <Loader2 class="h-5 w-5 animate-spin text-muted-foreground" />
      </div>

      <div
        v-if="!chatStore.messages.length"
        class="flex h-full min-h-105 flex-col items-center justify-center gap-4 px-6 text-center"
      >
        <div class="flex size-12 items-center justify-center rounded-full bg-primary/10">
          <Sparkles class="size-6 text-primary" />
        </div>
        <div class="max-w-md space-y-2">
          <h2 class="text-xl font-semibold">{{ $t('chat.welcomeTitle') }}</h2>
          <p class="text-sm text-muted-foreground">
            {{ $t('chat.welcomeSub') }}
          </p>
        </div>
        <div
          v-if="!documentsStore.hasDocuments"
          class="flex items-center gap-2 rounded-lg border border-dashed px-4 py-3 text-sm text-muted-foreground"
        >
          <FileText class="size-4" />
          {{ $t('chat.startUploadNotice') }}
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
        :title="$t('chat.jumpToLatest')"
        @click="scrollToBottom(true)"
      >
        <ArrowDown class="h-4 w-4 text-primary" />
        <span class="sr-only">{{ $t('chat.jumpToLatest') }}</span>
      </Button>
    </Transition>
  </div>
</template>
