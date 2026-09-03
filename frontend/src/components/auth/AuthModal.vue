<script setup lang="ts">
import { ref, watch } from "vue"
import { Loader2, Lock, Mail, User as UserIcon } from "lucide-vue-next"
import { useAuthStore } from "@/stores/auth"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

const isOpen = defineModel<boolean>("open", { default: false })
const authStore = useAuthStore()
const loginForm = ref({
  email: "",
  password: "",
})
const registerForm = ref({
  name: "",
  email: "",
  password: "",
})

watch(isOpen, () => {
  authStore.error = null
})

async function handleLogin() {
  authStore.error = null
  try {
    await authStore.login(loginForm.value)
    isOpen.value = false // Close modal on success
  } catch {
    // Error is handled via authStore.error
  }
}

async function handleRegister() {
  authStore.error = null
  try {
    await authStore.register(registerForm.value)
    isOpen.value = false // Close modal on success
  } catch {
    // Error is handled via authStore.error
  }
}
</script>

<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="sm:max-w-106.25">
      <DialogHeader>
        <DialogTitle class="text-xl">Authentication Optional</DialogTitle>
        <DialogDescription>
          Sign in or create an account to save your progress and access extra features.
        </DialogDescription>
      </DialogHeader>

      <!-- Global Auth Error Alert -->
      <div
        v-if="authStore.error"
        class="p-3 text-sm text-destructive bg-destructive/10 rounded-md border border-destructive/20 font-medium"
      >
        {{ authStore.error }}
      </div>

      <Tabs default-value="login" class="w-full mt-2">
        <TabsList class="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="login">Login</TabsTrigger>
          <TabsTrigger value="register">Register</TabsTrigger>
        </TabsList>

        <!-- LOGIN TAB -->
        <TabsContent value="login">
          <form @submit.prevent="handleLogin" class="space-y-4">
            <div class="space-y-2">
              <Label for="modal-login-email">Email</Label>
              <div class="relative">
                <Mail class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="modal-login-email"
                  v-model="loginForm.email"
                  type="email"
                  placeholder="m@example.com"
                  class="pl-9"
                  required
                />
              </div>
            </div>
            <div class="space-y-2">
              <Label for="modal-login-password">Password</Label>
              <div class="relative">
                <Lock class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="modal-login-password"
                  v-model="loginForm.password"
                  type="password"
                  class="pl-9"
                  required
                />
              </div>
            </div>
            <div class="pt-2 flex flex-col gap-2">
              <Button type="submit" class="w-full" :disabled="authStore.isLoading">
                <Loader2 v-if="authStore.isLoading" class="mr-2 h-4 w-4 animate-spin" />
                Sign In
              </Button>
              <Button type="button" variant="ghost" class="w-full" @click="isOpen = false">
                Continue as Guest
              </Button>
            </div>
          </form>
        </TabsContent>

        <!-- REGISTER TAB -->
        <TabsContent value="register">
          <form @submit.prevent="handleRegister" class="space-y-4">
            <div class="space-y-2">
              <Label for="modal-reg-name">Full Name</Label>
              <div class="relative">
                <UserIcon class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="modal-reg-name"
                  v-model="registerForm.name"
                  placeholder="John Doe"
                  class="pl-9"
                  required
                />
              </div>
            </div>
            <div class="space-y-2">
              <Label for="modal-reg-email">Email</Label>
              <div class="relative">
                <Mail class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="modal-reg-email"
                  v-model="registerForm.email"
                  type="email"
                  placeholder="m@example.com"
                  class="pl-9"
                  required
                />
              </div>
            </div>
            <div class="space-y-2">
              <Label for="modal-reg-password">Password</Label>
              <div class="relative">
                <Lock class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="modal-reg-password"
                  v-model="registerForm.password"
                  type="password"
                  class="pl-9"
                  required
                />
              </div>
            </div>
            <div class="pt-2 flex flex-col gap-2">
              <Button type="submit" class="w-full" :disabled="authStore.isLoading">
                <Loader2 v-if="authStore.isLoading" class="mr-2 h-4 w-4 animate-spin" />
                Create Account
              </Button>
              <Button type="button" variant="ghost" class="w-full" @click="isOpen = false">
                Continue as Guest
              </Button>
            </div>
          </form>
        </TabsContent>
      </Tabs>
    </DialogContent>
  </Dialog>
</template>