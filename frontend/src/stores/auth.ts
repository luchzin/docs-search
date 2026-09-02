import { defineStore } from "pinia"
import { ref, computed } from "vue"
import type { User } from "@/types"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem("auth_token"))
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  async function login(credentials: { email: string; password: string }) {
    isLoading.value = true
    error.value = null

    try {
      // TODO: Replace with your actual authentication API call
      // Example:
      // const response = await api.post("/auth/login", credentials)
      // const { user: userData, token: authToken } = response.data

      // Mock delay & successful auth payload:
      await new Promise((resolve) => setTimeout(resolve, 1000))
      
      const mockUser: User = {
        id: "usr_" + crypto.randomUUID(),
        email: credentials.email,
        username: credentials.email.split("@")[0],
      }
      const mockToken = "mock_jwt_token_" + Date.now()

      // Set state & persist token
      user.value = mockUser
      token.value = mockToken
      localStorage.setItem("auth_token", mockToken)

      return mockUser
    } catch (err: any) {
      error.value = err.response?.data?.message || err.message || "Failed to log in. Please try again."
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register a new user.
   * Replace the body inside try {} with your backend API request.
   */
  async function register(payload: { email: string; password: string; name?: string }) {
    isLoading.value = true
    error.value = null

    try {
      // TODO: Replace with your backend registration API call
      // Example:
      // const response = await api.post("/auth/register", payload)
      // const { user: userData, token: authToken } = response.data

      await new Promise((resolve) => setTimeout(resolve, 1000))

      const mockUser: User = {
        id: "usr_" + crypto.randomUUID(),
        email: payload.email,
        username: payload.name || payload.email.split("@")[0],
      }
      const mockToken = "mock_jwt_token_" + Date.now()

      user.value = mockUser
      token.value = mockToken
      localStorage.setItem("auth_token", mockToken)

      return mockUser
    } catch (err: any) {
      error.value = err.response?.data?.message || err.message || "Registration failed. Please try again."
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch current authenticated user (e.g. on initial app load / page refresh).
   */
  async function fetchCurrentUser() {
    if (!token.value) return null

    isLoading.value = true
    error.value = null

    try {
      // TODO: Replace with endpoint that gets current user from stored token
      // Example:
      // const response = await api.get("/auth/me")
      // user.value = response.data
      
      return user.value
    } catch (err: any) {
      // Clear token if invalid/expired
      logout()
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Log out current user and clear stored state/tokens.
   */
  function logout() {
    user.value = null
    token.value = null
    error.value = null
    localStorage.removeItem("auth_token")
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    fetchCurrentUser,
    logout,
  }
})