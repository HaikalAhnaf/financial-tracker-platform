<template>
  <div class="min-h-screen bg-brokenwhite font-sans text-darkpurple-dark transition-colors duration-300">
    <nav
      v-if="$route.path !== '/login'"
      class="bg-white border-b border-darkpurple/10 px-6 py-4 flex flex-col md:flex-row justify-between items-center mb-8 shadow-sm gap-4">
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded-full bg-darkpurple"></div>
        <h1 class="text-xl font-bold tracking-tight text-darkpurple-dark">Financial Tracker</h1>
      </div>

      <div class="flex items-center gap-6">
        <!-- Tagline: Shows the decoded Cognito JWT name -->
        <div class="hidden lg:block text-sm text-darkpurple-light">
          Welcome back,
          <span class="font-bold text-darkpurple-dark">{{ authStore.user?.name || "User" }}</span>
        </div>

        <div class="h-4 w-px bg-darkpurple/10 hidden lg:block"></div>

        <NuxtLink to="/" class="text-darkpurple-light hover:text-darkpurple font-semibold transition-colors" activeClass="text-darkpurple font-bold">
          Dashboard
        </NuxtLink>
        <NuxtLink
          to="/history"
          class="text-darkpurple-light hover:text-darkpurple font-semibold transition-colors"
          activeClass="text-darkpurple font-bold">
          History
        </NuxtLink>
        <NuxtLink
          to="/settings"
          class="text-darkpurple-light hover:text-darkpurple font-semibold transition-colors"
          activeClass="text-darkpurple font-bold">
          Settings
        </NuxtLink>

        <!-- Logout Button -->
        <button
          @click="authStore.logout"
          class="bg-rose-50 text-rose-600 hover:bg-rose-100 px-4 py-2 rounded-xl text-sm font-bold transition-colors ml-2 shadow-sm">
          Log Out
        </button>
      </div>
    </nav>

    <main class="max-w-6xl mx-auto px-4">
      <slot />
    </main>
  </div>
</template>

<script setup>
  import { onMounted } from "vue";
  import { useAuthStore } from "~/stores/auth";

  const authStore = useAuthStore();

  onMounted(() => {
    authStore.initAuth();
  });
</script>
