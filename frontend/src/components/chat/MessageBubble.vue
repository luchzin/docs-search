<script setup lang="ts">
import { Bot, User } from "@lucide/vue"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { ChatMessage } from "@/types"

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <div
    :class="
      cn(
        'flex gap-2.5 sm:gap-3 px-3 py-4 sm:px-4 sm:py-5',
        message.role === 'assistant' ? 'bg-muted/30' : 'bg-background',
      )
    "
  >
    <Avatar class="size-7 sm:size-8 shrink-0">
      <AvatarFallback
        :class="
          cn(
            message.role === 'assistant'
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground',
          )
        "
      >
        <Bot v-if="message.role === 'assistant'" class="size-3.5 sm:size-4" />
        <User v-else class="size-3.5 sm:size-4" />
      </AvatarFallback>
    </Avatar>

    <div class="min-w-0 flex-1 space-y-1">
      <p class="text-xs sm:text-sm font-medium">
        {{ message.role === "assistant" ? "Assistant" : "You" }}
      </p>
      <p class="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90 wrap-break-word">
        {{ message.content }}
      </p>
    </div>
  </div>
</template>
