export default defineNuxtConfig({
  compatibilityDate: "2024-04-03",
  devtools: { enabled: true },
  ssr: false,
  modules: ["@nuxtjs/tailwindcss", "@pinia/nuxt"],
  runtimeConfig: {
    public: {
      appVersion: process.env.APP_VERSION || "v1.0.0-dev",
      apiUrl: process.env.API || "",
      cognitoUserPoolId: process.env.COGNITO_USER_POOL_ID || "",
      cognitoClientId: process.env.COGNITO_CLIENT_ID || "",
    },
  },
  vite: {
    optimizeDeps: {
      include: ["chart.js", "vue-chartjs"],
    },
  },
});
