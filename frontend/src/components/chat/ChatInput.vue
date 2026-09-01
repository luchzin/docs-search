<script setup lang="ts">
import { ref } from "vue";
import { ArrowUp } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/stores/chat";
import { useDocumentsStore } from "@/stores/documents";

const chatStore = useChatStore();
const documentsStore = useDocumentsStore();

const input = ref("");

async function submit() {
  const content = input.value;
  if (!content.trim()) return;

  input.value = "";
  await chatStore.sendMessage(content);
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit();
  }
}
</script>

<template>
  <div class="border-t bg-background px-3 py-3 sm:px-4 sm:py-4">
    <p
      v-if="chatStore.error"
      class="mb-2 text-center text-xs sm:text-sm text-destructive"
    >
      {{ chatStore.error }}
    </p>

    <div
      class="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border bg-card p-1.5 sm:p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring"
    >
      <Textarea
        v-model="input"
        rows="1"
        placeholder="Ask a question about your documents..."
        class="max-h-36 sm:max-h-40 min-h-10 sm:min-h-11 resize-none border-0 bg-transparent py-2 text-sm shadow-none focus-visible:ring-0"
        :disabled="chatStore.isLoading"
        @keydown="onKeydown"
      />
      <Button
        size="icon"
        class="h-9 w-9 sm:h-10 sm:w-10 shrink-0 rounded-xl"
        :disabled="
          !input.trim() || chatStore.isLoading || !documentsStore.hasDocuments
        "
        @click="submit"
      >
        <ArrowUp class="size-4" />
        <span class="sr-only">Send message</span>
      </Button>
    </div>

    <p class="mt-2 text-center text-[11px] sm:text-xs text-muted-foreground">
      Answers are generated from your uploaded PDF documents
    </p>
  </div>
</template>
