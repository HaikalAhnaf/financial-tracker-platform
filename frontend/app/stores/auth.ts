import { defineStore } from "pinia";
import { useRouter } from "vue-router";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: null as string | null,
    user: null as { name: string; email: string } | null,
    guestSession: null as string | null, // NEW: Tracks the temporary UUID
  }),
  getters: {
    // NEW: Centralized header generator for API calls
    authHeaders(state) {
      const headers: Record<string, string> = {};
      if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
      }
      if (state.guestSession) {
        headers["X-Guest-Session"] = state.guestSession;
      }
      return headers;
    },
  },
  actions: {
    initAuth() {
      if (process.client) {
        const storedToken = localStorage.getItem("auth_token");
        const storedGuestSession = localStorage.getItem("guest_session");

        if (storedToken) {
          this.token = storedToken;
          this.decodeToken(storedToken);
        }
        if (storedGuestSession) {
          this.guestSession = storedGuestSession;
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
    setGuestSession(sessionId: string) {
      this.guestSession = sessionId;
      if (process.client) {
        localStorage.setItem("guest_session", sessionId);
      }
    },
    decodeToken(token: string) {
      try {
        const payloadPart = token.split(".")[1];

        if (!payloadPart) {
          throw new Error("Invalid JWT format");
        }

        const payload = JSON.parse(atob(payloadPart));

        this.user = {
          name: payload.name || "User",
          email: payload.email || "",
        };
      } catch (e) {
        this.logout();
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      this.guestSession = null;

      if (process.client) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("guest_session");
      }

      navigateTo("/login");
    },
  },
});
