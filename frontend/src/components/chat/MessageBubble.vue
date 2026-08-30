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
        'flex gap-3 px-4 py-5',
        message.role === 'assistant' ? 'bg-muted/30' : 'bg-background',
      )
    "
  >
    <Avatar class="size-8 shrink-0">
      <AvatarFallback
        :class="
          cn(
            message.role === 'assistant'
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground',
          )
        "
      >
        <Bot v-if="message.role === 'assistant'" class="size-4" />
        <User v-else class="size-4" />
      </AvatarFallback>
    </Avatar>

    <div class="min-w-0 flex-1 space-y-1">
      <p class="text-sm font-medium">
        {{ message.role === "assistant" ? "Assistant" : "You" }}
      </p>
      <p class="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
        {{ message.content }}
      </p>
    </div>
  </div>
</template>
