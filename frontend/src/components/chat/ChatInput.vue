<script setup lang="ts">
import { ref } from "vue"
import { ArrowUp } from "@lucide/vue"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useChatStore } from "@/stores/chat"
import { useDocumentsStore } from "@/stores/documents"

const chatStore = useChatStore()
const documentsStore = useDocumentsStore()

const input = ref("")

async function submit() {
  const content = input.value
  if (!content.trim()) return

  input.value = ""
  await chatStore.sendMessage(content)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <div class="border-t bg-background px-4 py-4">
    <p v-if="chatStore.error" class="mb-2 text-center text-sm text-destructive">
      {{ chatStore.error }}
    </p>

    <div class="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border bg-card p-2 shadow-sm">
      <Textarea
        v-model="input"
        rows="1"
        placeholder="Ask a question about your documents..."
        class="max-h-40 min-h-11 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
        :disabled="chatStore.isLoading"
        @keydown="onKeydown"
      />
      <Button
        size="icon"
        class="shrink-0 rounded-xl"
        :disabled="!input.trim() || chatStore.isLoading || !documentsStore.hasDocuments"
        @click="submit"
      >
        <ArrowUp class="size-4" />
        <span class="sr-only">Send message</span>
      </Button>
    </div>

    <p class="mt-2 text-center text-xs text-muted-foreground">
      Answers are generated from your uploaded PDF documents
    </p>
  </div>
</template>
