import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types";
import { api } from "../lib/utils";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem("access_token"));
  const refreshToken = ref<string | null>(
    localStorage.getItem("refresh_token"),
  );
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isAuthenticated = computed(() => !!token.value && !!user.value);
  async function login(credentials: { email: string; password: string }) {
    isLoading.value = true;
    error.value = null;

    try {
      // Djoser JWT login endpoint
      const response = await api.post("/auth/jwt/create/", {
        email: credentials.email,
        username: credentials.email,
        password: credentials.password,
      });

      const { access, refresh } = response.data;
      token.value = access;
      refreshToken.value = refresh;
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);

      await fetchCurrentUser();

      return user.value;
    } catch (err: any) {
      const apiErrors = err.response?.data;
      if (apiErrors && typeof apiErrors === "object") {
        error.value =
          apiErrors.detail ||
          apiErrors.non_field_errors?.[0] ||
          Object.values(apiErrors).flat().join(" ");
      } else {
        error.value = "Failed to log in. Please check your credentials.";
      }
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function register(payload: {
    email: string;
    password: string;
    username?: string;
  }) {
    isLoading.value = true;
    error.value = null;

    try {
      const rawUsername = payload.username || payload.email.split("@")[0];
      const username = rawUsername.trim().replace(/\s+/g, "_");
      const response = await api.post("/auth/users/", {
        email: payload.email,
        username,
        password: payload.password,
        re_password: payload.password,
      });

      await login({ email: payload.email, password: payload.password });

      return response.data;
    } catch (err: any) {
      const apiErrors = err.response?.data;
      error.value =
        typeof apiErrors === "object"
          ? Object.values(apiErrors).flat().join(" ")
          : "Registration failed. Please try again.";
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return null;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>("/auth/users/me/");
      user.value = response.data;
      console.log(response.data);
      return user.value;
    } catch (err: any) {
      logout();
    } finally {
      isLoading.value = false;
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    refreshToken.value = null;
    error.value = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  return {
    user,
    token,
    refreshToken,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    fetchCurrentUser,
    logout,
  };
});
