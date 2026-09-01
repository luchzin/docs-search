<script setup lang="ts">
import { ref } from "vue"
import { FileText, Upload, X } from "@lucide/vue"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useDocumentsStore } from "@/stores/documents"

const documentsStore = useDocumentsStore()

const isDragging = ref(false)
const uploadError = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

async function handleFiles(files: FileList | File[]) {
  uploadError.value = null

  for (const file of files) {
    const error = await documentsStore.addDocument(file)
    if (error) uploadError.value = error
  }
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false
  if (event.dataTransfer?.files.length) {
    handleFiles(event.dataTransfer.files)
  }
}

function onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    handleFiles(input.files)
    input.value = ""
  }
}

function openFilePicker() {
  fileInput.value?.click()
}
</script>

<template>
  <div class="space-y-3">
    <div
      role="button"
      tabindex="0"
      :class="
        cn(
          'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-4 py-5 sm:py-6 text-center transition-colors',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/50',
        )
      "
      @click="openFilePicker"
      @keydown.enter="openFilePicker"
      @keydown.space.prevent="openFilePicker"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop="onDrop"
    >
      <Upload class="size-5 text-muted-foreground" />
      <div class="space-y-1">
        <p class="text-sm font-medium">Drop PDF here</p>
        <p class="text-xs text-muted-foreground">or click to browse</p>
      </div>
      <Badge variant="secondary" class="text-[11px] sm:text-xs">PDF only</Badge>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="application/pdf,.pdf"
      multiple
      class="hidden"
      @change="onFileSelect"
    />

    <p v-if="uploadError" class="text-xs text-destructive">
      {{ uploadError }}
    </p>

    <ul v-if="documentsStore.documents.length" class="space-y-2">
      <li
        v-for="doc in documentsStore.documents"
        :key="doc.id"
        class="flex items-start gap-2 rounded-md border bg-card p-2 sm:p-2.5"
      >
        <FileText class="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <div class="min-w-0 flex-1">
          <p class="truncate text-xs sm:text-sm font-medium">{{ doc.name }}</p>
          <p class="text-[11px] sm:text-xs text-muted-foreground">
            {{ documentsStore.formatFileSize(doc.size) }}
          </p>
          <Skeleton
            v-if="doc.status === 'uploading' || doc.status === 'processing'"
            class="mt-2 h-1.5 w-full"
          />
          <p
            v-else-if="doc.status === 'error'"
            class="mt-1 text-[11px] sm:text-xs text-destructive"
          >
            {{ doc.errorMessage }}
          </p>
          <Badge
            v-else-if="doc.status === 'ready'"
            variant="secondary"
            class="mt-1 text-[11px] sm:text-xs"
          >
            Ready
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          class="shrink-0"
          @click.stop="documentsStore.removeDocument(doc.id)"
        >
          <X class="size-3.5" />
          <span class="sr-only">Remove {{ doc.name }}</span>
        </Button>
      </li>
    </ul>
  </div>
</template>
