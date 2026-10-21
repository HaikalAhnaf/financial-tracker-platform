import { defineStore } from "pinia";
import { useAuthStore } from "./auth";

export interface Category {
  SK: string;
  name: string;
  type: "income" | "expense";
}

export const useCategoryStore = defineStore("category", {
  state: () => ({
    categories: [] as Category[],
    isLoading: false,
    error: null as string | null,
  }),
  getters: {
    expenseCategories: (state) => state.categories.filter((c) => c.type === "expense"),
    incomeCategories: (state) => state.categories.filter((c) => c.type === "income"),
  },
  actions: {
    async fetchCategories() {
      const config = useRuntimeConfig();
      const authStore = useAuthStore();
      this.isLoading = true;

      try {
        const data = await $fetch<{ categories: Category[] }>(`${config.public.apiUrl}?entity=category`, {
          headers: authStore.authHeaders,
        });
        this.categories = data.categories || [];
      } catch (err) {
        this.error = "Failed to load categories";
      } finally {
        this.isLoading = false;
      }
    },
    async addCategory(name: string, type: "income" | "expense") {
      const config = useRuntimeConfig();
      const authStore = useAuthStore();
      try {
        await $fetch(`${config.public.apiUrl}?entity=category`, {
          method: "POST",
          headers: authStore.authHeaders,
          body: { name, type },
        });
        await this.fetchCategories();
      } catch (err) {
        throw new Error("Failed to add category");
      }
    },
    async deleteCategory(sk: string) {
      const config = useRuntimeConfig();
      const authStore = useAuthStore();
      try {
        await $fetch(`${config.public.apiUrl}?entity=category`, {
          method: "DELETE",
          headers: authStore.authHeaders,
          body: { sk },
        });
        await this.fetchCategories();
      } catch (err) {
        throw new Error("Failed to delete category");
      }
    },
  },
});
