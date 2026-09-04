<script setup lang="ts">
import { ref, computed, nextTick } from "vue"
import {
  MessageSquarePlus,
  PanelLeftClose,
  MessageSquare,
  Pencil,
  Trash2,
  Check,
  X
} from "@lucide/vue"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/stores/chat"
import type { Chat } from "@/types"
import DocumentDropzone from "./DocumentDropzone.vue"

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

const chatStore = useChatStore()

const editingChatId = ref<string | null>(null)
const editingTitle = ref("")
const editInputRef = ref<HTMLInputElement | null>(null)

interface ChatGroup {
  label: string
  chats: Chat[]
}

const chatGroups = computed<ChatGroup[]>(() => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterdayStart = todayStart - 86400000
  const sevenDaysAgo = todayStart - 6 * 86400000

  const today: Chat[] = []
  const yesterday: Chat[] = []
  const previous7Days: Chat[] = []
  const older: Chat[] = []

  const sorted = [...chatStore.chats].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )

  for (const chat of sorted) {
    const chatTime = new Date(chat.updated_at).getTime()
    if (chatTime >= todayStart) {
      today.push(chat)
    } else if (chatTime >= yesterdayStart) {
      yesterday.push(chat)
    } else if (chatTime >= sevenDaysAgo) {
      previous7Days.push(chat)
    } else {
      older.push(chat)
    }
  }

  const groups: ChatGroup[] = []
  if (today.length > 0) groups.push({ label: "Today", chats: today })
  if (yesterday.length > 0) groups.push({ label: "Yesterday", chats: yesterday })
  if (previous7Days.length > 0) groups.push({ label: "Previous 7 Days", chats: previous7Days })
  if (older.length > 0) groups.push({ label: "Older", chats: older })

  return groups
})

function handleNewChat() {
  chatStore.createNewChat()
}

function selectChat(id: string) {
  if (editingChatId.value === id) return
  chatStore.selectChat(id)
}

async function startRenaming(chat: Chat, e: Event) {
  e.stopPropagation()
  editingChatId.value = chat.id
  editingTitle.value = chat.title
  await nextTick()
  editInputRef.value?.focus()
}

function saveRename(id: string) {
  if (editingChatId.value === id) {
    chatStore.renameChat(id, editingTitle.value)
    editingChatId.value = null
  }
}

function cancelRename() {
  editingChatId.value = null
}

function handleDeleteChat(id: string, e: Event) {
  e.stopPropagation()
  chatStore.deleteChat(id)
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
    <!-- Header -->
    <div class="flex items-center justify-between p-3">
      <h1 class="truncate text-sm font-semibold">Doc Chat</h1>
      <Button variant="ghost" size="icon-sm" @click="emit('toggle')">
        <PanelLeftClose class="size-4" />
        <span class="sr-only">Close sidebar</span>
      </Button>
    </div>

    <!-- New Chat Button -->
    <div class="px-3 pb-3">
      <Button
        variant="outline"
        class="w-full justify-start gap-2 border-dashed shadow-xs hover:bg-accent hover:text-accent-foreground"
        @click="handleNewChat"
      >
        <MessageSquarePlus class="size-4" />
        <span>New chat</span>
      </Button>
    </div>

    <Separator />

    <!-- Chat History & Documents List -->
    <div class="flex-1 overflow-y-auto px-3 py-2 space-y-4">
      <!-- Chat History Section -->
      <div>
        <p class="mb-2 px-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Chat History
        </p>

        <div v-if="!chatStore.chats.length" class="px-2 py-3 text-xs text-muted-foreground text-center rounded-md border border-dashed">
          No chats yet. Start a new chat above!
        </div>

        <div v-else class="space-y-3">
          <div v-for="group in chatGroups" :key="group.label" class="space-y-1">
            <p class="px-1 text-[10px] font-medium text-muted-foreground/80 uppercase tracking-wider">
              {{ group.label }}
            </p>
            <div
              v-for="chat in group.chats"
              :key="chat.id"
              :class="
                cn(
                  'group relative flex items-center justify-between rounded-lg px-2.5 py-2 text-xs transition-colors cursor-pointer select-none',
                  chatStore.activeChatId === chat.id
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                    : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground'
                )
              "
              @click="selectChat(chat.id)"
            >
              <!-- Editing Mode -->
              <template v-if="editingChatId === chat.id">
                <div class="flex items-center gap-1.5 w-full" @click.stop>
                  <Input
                    ref="editInputRef"
                    v-model="editingTitle"
                    class="h-7 text-xs px-2 py-0"
                    @keyup.enter="saveRename(chat.id)"
                    @keyup.esc="cancelRename"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-6 w-6 shrink-0"
                    @click="saveRename(chat.id)"
                  >
                    <Check class="size-3 text-green-600" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-6 w-6 shrink-0"
                    @click="cancelRename"
                  >
                    <X class="size-3 text-muted-foreground" />
                  </Button>
                </div>
              </template>

              <!-- Display Mode -->
              <template v-else>
                <div class="flex items-center gap-2 min-w-0 pr-1 flex-1">
                  <MessageSquare class="size-3.5 shrink-0 opacity-70" />
                  <span class="truncate">{{ chat.title }}</span>
                </div>

                <!-- Hover actions (Edit & Delete) -->
                <div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity gap-0.5 shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-6 w-6 text-muted-foreground hover:text-foreground"
                    title="Rename chat"
                    @click="startRenaming(chat, $event)"
                  >
                    <Pencil class="size-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-6 w-6 text-muted-foreground hover:text-destructive"
                    title="Delete chat"
                    @click="handleDeleteChat(chat.id, $event)"
                  >
                    <Trash2 class="size-3" />
                  </Button>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      <!-- Documents Section -->
      <div>
        <p class="mb-2 px-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Documents
        </p>
        <DocumentDropzone />
      </div>
    </div>
  </aside>
</template>
