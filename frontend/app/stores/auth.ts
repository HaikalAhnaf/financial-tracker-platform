import { defineStore } from "pinia";
import { useRouter } from "vue-router";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: null as string | null,
    user: null as { name: string; email: string } | null,
  }),
  actions: {
    initAuth() {
      if (process.client) {
        const storedToken = localStorage.getItem("auth_token");
        if (storedToken) {
          this.token = storedToken;
          this.decodeToken(storedToken);
        }
      }
    },
    setToken(token: string) {
      this.token = token;
      if (process.client) {
        localStorage.setItem("auth_token", token);
      }
      this.decodeToken(token);
    },
    decodeToken(token: string) {
      try {
        // Extract the payload (the second part of the JWT)
        const payloadPart = token.split(".")[1];

        // Explicitly check if it exists so TypeScript knows it is definitely a string
        if (!payloadPart) {
          throw new Error("Invalid JWT format");
        }

        // Now TypeScript is happy because payloadPart is guaranteed to be a string
        const payload = JSON.parse(atob(payloadPart));

        this.user = {
          name: payload.name || "User",
          email: payload.email || "",
        };
      } catch (e) {
        this.logout(); // If the token is invalid or tampered with, force a logout
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      if (process.client) {
        localStorage.removeItem("auth_token");
      }

      // Use Nuxt's global navigation helper instead of useRouter
      navigateTo("/login");
    },
  },
});
