<script setup lang="ts">
import { ref, computed, nextTick } from "vue"
import {
  MessageSquarePlus,
  PanelLeftClose,
  MessageSquare,
  FileText,
  Pencil,
  Trash2,
  Check,
  X,
  Settings
} from "@lucide/vue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/stores/chat"
import { useDocumentsStore } from "@/stores/documents"
import { useModelStore } from "@/stores/model"
import type { Chat } from "@/types"
import DocumentDropzone from "./DocumentDropzone.vue"

defineProps<{
  open: boolean
  currentView?: "chat" | "settings"
}>()

const emit = defineEmits<{
  toggle: []
  openSettings: []
  openChat: []
}>()

const chatStore = useChatStore()
const documentsStore = useDocumentsStore()
const modelStore = useModelStore()

const activeTab = ref<"chats" | "docs">("chats")
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
  emit('openChat')
}

function selectChat(id: string) {
  if (editingChatId.value === id) return
  chatStore.selectChat(id)
  emit('openChat')
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
    <div class="flex h-14 shrink-0 items-center justify-between px-3 border-b border-sidebar-border">
      <div class="flex items-center gap-2">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary text-secondary-foreground font-bold shadow-2xs">
          <MessageSquare class="size-4" />
        </div>
        <h1 class="truncate text-sm font-bold">Doc Chat</h1>
      </div>
      <Button variant="ghost" size="icon-sm" @click="emit('toggle')">
        <PanelLeftClose class="size-4" />
        <span class="sr-only">Close sidebar</span>
      </Button>
    </div>

    <!-- Segmented Tab Navigation Switcher -->
    <div class="px-3 py-2 border-b border-sidebar-border shrink-0">
      <div class="grid grid-cols-2 gap-1 rounded-lg bg-muted/60 p-1 text-xs">
        <button
          type="button"
          :class="
            cn(
              'flex items-center justify-center gap-1.5 rounded-md py-1.5 px-2 text-xs transition-all cursor-pointer',
              activeTab === 'chats'
                ? 'bg-secondary text-secondary-foreground font-semibold shadow-2xs'
                : 'text-muted-foreground hover:text-foreground font-medium'
            )
          "
          @click="activeTab = 'chats'"
        >
          <MessageSquare class="size-3.5" />
          <span>Chats</span>
          <span
            v-if="chatStore.chats.length"
            class="ml-0.5 rounded-full bg-black/10 dark:bg-black/20 px-1.5 py-0.2 text-[10px] font-bold"
          >
            {{ chatStore.chats.length }}
          </span>
        </button>

        <button
          type="button"
          :class="
            cn(
              'flex items-center justify-center gap-1.5 rounded-md py-1.5 px-2 text-xs transition-all cursor-pointer',
              activeTab === 'docs'
                ? 'bg-secondary text-secondary-foreground font-semibold shadow-2xs'
                : 'text-muted-foreground hover:text-foreground font-medium'
            )
          "
          @click="activeTab = 'docs'"
        >
          <FileText class="size-3.5" />
          <span>Docs</span>
          <span
            v-if="documentsStore.documents.length"
            class="ml-0.5 rounded-full bg-black/10 dark:bg-black/20 px-1.5 py-0.2 text-[10px] font-bold"
          >
            {{ documentsStore.documents.length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Tab 1: Chat Sessions List -->
    <div v-if="activeTab === 'chats'" class="flex-1 flex flex-col min-h-0">
      <div class="p-3 pb-2 shrink-0">
        <Button
          variant="outline"
          class="w-full justify-start gap-2 border-dashed shadow-2xs hover:bg-accent hover:text-accent-foreground"
          @click="handleNewChat"
        >
          <MessageSquarePlus class="size-4" />
          <span>New chat</span>
        </Button>
      </div>

      <div class="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        <div v-if="!chatStore.chats.length" class="px-2 py-4 text-xs text-muted-foreground text-center rounded-md border border-dashed">
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
                    ? 'bg-sidebar-accent text-foreground font-semibold border-l-2 border-secondary pl-2'
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
    </div>

    <!-- Tab 2: Documents List & Upload -->
    <div v-else class="flex-1 overflow-y-auto p-3 min-h-0">
      <DocumentDropzone />
    </div>

    <!-- Sidebar Footer / Settings -->
    <div class="p-3 border-t border-sidebar-border shrink-0">
      <button
        type="button"
        :class="
          cn(
            'flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors cursor-pointer select-none',
            currentView === 'settings'
              ? 'bg-secondary text-secondary-foreground font-semibold shadow-2xs'
              : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground'
          )
        "
        @click="emit('openSettings')"
      >
        <div class="flex items-center gap-2">
          <Settings class="size-4 opacity-80" />
          <span>Settings</span>
        </div>
        <span class="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded font-mono truncate max-w-24">
          {{ modelStore.selectedModel.name }}
        </span>
      </button>
    </div>
  </aside>
</template>
