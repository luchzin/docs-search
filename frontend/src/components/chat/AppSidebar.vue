<script setup lang="ts">
import { MessageSquarePlus, PanelLeftClose, PanelLeftOpen } from "@lucide/vue"
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
  <aside
    :class="
      cn(
        'flex h-full shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200',
        open ? 'w-72' : 'w-0 overflow-hidden border-r-0',
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

  <Button
    v-if="!open"
    variant="outline"
    size="icon-sm"
    class="absolute left-3 top-3 z-10"
    @click="emit('toggle')"
  >
    <PanelLeftOpen class="size-4" />
    <span class="sr-only">Open sidebar</span>
  </Button>
</template>
