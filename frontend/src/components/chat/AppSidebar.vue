<script setup lang="ts">
import { MessageSquarePlus, PanelLeftClose } from "@lucide/vue"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/stores/chat"
import DocumentDropzone from "./DocumentDropzone.vue"

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

const chatStore = useChatStore()

function startNewChat() {
  chatStore.clearMessages()
}
</script>

<template>
  <!-- Mobile Backdrop Overlay -->
  <Transition
    enter-active-class="transition-opacity ease-linear duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity ease-linear duration-200"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="open"
      class="fixed inset-0 z-40 bg-background/80 backdrop-blur-xs md:hidden"
      @click="emit('toggle')"
    />
  </Transition>

  <aside
    :class="
      cn(
        'fixed inset-y-0 left-0 z-50 flex h-full flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200 ease-in-out md:relative md:z-0',
        open
          ? 'w-72 translate-x-0 shadow-xl md:shadow-none'
          : '-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:border-r-0',
      )
    "
  >
    <div class="flex items-center justify-between p-3">
      <h1 class="truncate text-sm font-semibold">Doc Chat</h1>
      <Button variant="ghost" size="icon-sm" @click="emit('toggle')">
        <PanelLeftClose class="size-4" />
        <span class="sr-only">Close sidebar</span>
      </Button>
    </div>

    <div class="px-3 pb-3">
      <Button
        variant="outline"
        class="w-full justify-start gap-2"
        @click="startNewChat"
      >
        <MessageSquarePlus class="size-4" />
        New chat
      </Button>
    </div>

    <Separator />

    <div class="flex-1 overflow-y-auto p-3">
      <p class="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Documents
      </p>
      <DocumentDropzone />
    </div>
  </aside>
</template>
