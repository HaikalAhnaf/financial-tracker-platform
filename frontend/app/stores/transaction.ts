import { defineStore } from "pinia";
import { useAuthStore } from "./auth";

export interface Transaction {
  SK?: string;
  category: string;
  amount: number | string;
  type: string;
  note?: string;
  timestamp: string | number;
}

export const useTransactionStore = defineStore("transaction", {
  state: () => {
    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;

    return {
      transactions: [] as Transaction[],
      historyTransactions: [] as Transaction[],
      serverBalance: 0,
      isLoading: false,
      error: null as string | null,
      selectedMonth: currentMonth,
      historyRange: "6m",
      customStartDate: "", // New
      customEndDate: "", // New
    };
  },
  getters: {
    totalIncome(state): number {
      return state.transactions.filter((t) => t.type === "income").reduce((sum, t) => sum + Number(t.amount), 0);
    },
    totalExpense(state): number {
      return state.transactions.filter((t) => t.type === "expense").reduce((sum, t) => sum + Number(t.amount), 0);
    },
    expensesByCategory(state): Record<string, number> {
      return state.transactions
        .filter((t) => t.type === "expense")
        .reduce((acc: Record<string, number>, txn) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        }, {});
    },
    incomeByCategory(state): Record<string, number> {
      return state.transactions
        .filter((t) => t.type === "income")
        .reduce((acc: Record<string, number>, txn) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        }, {});
    },
    recentTransactions(state): Transaction[] {
      return state.transactions.slice(0, 5);
    },
  },
  actions: {
    async fetchTransactions() {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;
      const authStore = useAuthStore();

      this.isLoading = true;
      this.error = null;
      try {
        const data = await $fetch<{ balance: number; transactions: Transaction[] }>(`${apiUrl}?month=${this.selectedMonth}`, {
          headers: authStore.authHeaders,
        });

        this.serverBalance = data.balance || 0;
        this.transactions = (data.transactions || []).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      } catch (err) {
        this.error = "Error loading transactions.";
      } finally {
        this.isLoading = false;
      }
    },
    async fetchHistory() {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;
      const authStore = useAuthStore();

      this.isLoading = true;
      this.error = null;

      try {
        let url = `${apiUrl}?range=${this.historyRange}`;

        // If custom range is selected and dates are provided, use those instead
        if (this.historyRange === "custom" && this.customStartDate && this.customEndDate) {
          url = `${apiUrl}?startDate=${this.customStartDate}&endDate=${this.customEndDate}`;
        }

        const data = await $fetch<{ balance: number; transactions: Transaction[] }>(url, {
          headers: authStore.authHeaders,
        });
        this.serverBalance = data.balance || 0;
        this.historyTransactions = (data.transactions || []).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      } catch (err) {
        this.error = "Error loading history.";
      } finally {
        this.isLoading = false;
      }
    },
    async addTransaction(newTxn: Partial<Transaction>) {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;
      const authStore = useAuthStore();

      try {
        await $fetch(apiUrl, {
          method: "POST",
          headers: authStore.authHeaders,
          body: newTxn,
        });
        await this.fetchTransactions();
      } catch (err) {
        throw new Error("Failed to add transaction");
      }
    },
    async updateNote(sk: string, note: string) {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;
      const authStore = useAuthStore();

      try {
        await $fetch(apiUrl, {
          method: "PUT",
          headers: authStore.authHeaders,
          body: { sk, note },
        });
        await this.fetchHistory();
      } catch (err) {
        throw new Error("Failed to update note");
      }
    },
    async deleteTransaction(sk: string) {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;
      const authStore = useAuthStore();

      try {
        await $fetch(apiUrl, {
          method: "DELETE",
          headers: authStore.authHeaders,
          body: { sk },
        });
        await this.fetchTransactions();
        await this.fetchHistory();
      } catch (err) {
        throw new Error("Failed to delete transaction");
      }
    },
  },
});
