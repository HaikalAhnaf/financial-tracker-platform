<template>
  <div class="min-h-screen bg-brokenwhite font-sans text-darkpurple-dark transition-colors duration-300">
    <nav class="bg-white border-b border-darkpurple/10 px-6 py-4 flex justify-between items-center mb-8 shadow-sm">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-darkpurple"></div>
        <h1 class="text-xl font-bold tracking-tight text-darkpurple-dark">Financial Tracker</h1>
      </div>
      <div class="flex gap-6">
        <NuxtLink to="/" class="text-darkpurple-light hover:text-darkpurple font-semibold transition-colors">Dashboard</NuxtLink>
        <NuxtLink to="/settings" class="text-darkpurple-light hover:text-darkpurple font-semibold transition-colors">Settings</NuxtLink>
      </div>
    </nav>

    <main class="max-w-6xl mx-auto px-4">
      <slot />
    </main>
  </div>
</template>
