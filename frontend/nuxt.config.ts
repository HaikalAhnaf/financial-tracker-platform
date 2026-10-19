export default defineNuxtConfig({
  compatibilityDate: "2024-04-03",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@pinia/nuxt"],
  runtimeConfig: {
    public: {
      // Maps process.env.API from your frontend/.env file
      apiUrl: process.env.API || "",
    },
  },
  vite: {
    optimizeDeps: {
      include: ["chart.js", "vue-chartjs"],
    },
  },
});
