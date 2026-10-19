import { defineStore } from "pinia";

export const useTransactionStore = defineStore("transaction", {
  state: () => ({
    transactions: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchTransactions() {
      this.isLoading = true;
      this.error = null;
      try {
        const data = await $fetch("https://sf2bukjp9b.execute-api.ap-southeast-1.amazonaws.com");
        this.transactions = (data.transactions || []).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      } catch (err) {
        this.error = "Error loading transactions.";
      } finally {
        this.isLoading = false;
      }
    },
    async addTransaction(newTxn) {
      try {
        await $fetch("https://sf2bukjp9b.execute-api.ap-southeast-1.amazonaws.com", {
          method: "POST",
          body: newTxn,
        });
        await this.fetchTransactions(); // Refresh the global state
      } catch (err) {
        throw new Error("Failed to add transaction");
      }
    },
  },
});
