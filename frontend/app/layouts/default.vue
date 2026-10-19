<template>
  <div class="min-h-screen bg-gray-100 font-sans">
    <nav class="bg-white shadow px-8 py-4 flex justify-between items-center mb-8">
      <h1 class="text-xl font-bold text-gray-800">Cloud Financial Tracker</h1>
      <div class="flex gap-6">
        <NuxtLink to="/" class="text-gray-600 hover:text-blue-600 font-medium">Dashboard</NuxtLink>
        <NuxtLink to="/settings" class="text-gray-600 hover:text-blue-600 font-medium">Settings</NuxtLink>
      </div>
    </nav>

    <main class="max-w-3xl mx-auto px-4">
      <slot />
    </main>
  </div>
</template>
