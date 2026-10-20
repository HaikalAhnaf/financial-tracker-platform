import { useAuthStore } from "~/stores/auth";

export default defineNuxtRouteMiddleware((to) => {
  // Only check on the client-side where localStorage exists
  if (process.client) {
    const authStore = useAuthStore();
    authStore.initAuth();

    const isAuthenticated = !!authStore.token;

    // If not logged in and trying to access a protected page, redirect to Login
    if (!isAuthenticated && to.path !== "/login") {
      return navigateTo("/login");
    }

    // If logged in and trying to access the Login page, redirect to Dashboard
    if (isAuthenticated && to.path === "/login") {
      return navigateTo("/");
    }
  }
});
