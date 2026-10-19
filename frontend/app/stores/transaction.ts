import { defineStore } from "pinia";

export interface Transaction {
  SK?: string;
  category: string;
  amount: number | string;
  type: string;
  timestamp: string | number;
}

export const useTransactionStore = defineStore("transaction", {
  state: () => {
    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;

    return {
      transactions: [] as Transaction[],
      isLoading: false,
      error: null as string | null,
      selectedMonth: currentMonth,
    };
  },
  getters: {
    filteredTransactions: (state) => {
      return state.transactions.filter((t) => {
        const date = new Date(t.timestamp);
        const txnMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        return txnMonth === state.selectedMonth;
      });
    },

    totalIncome(): number {
      return this.filteredTransactions
        .filter((t: Transaction) => t.type === "income")
        .reduce((sum: number, t: Transaction) => sum + Number(t.amount), 0);
    },

    totalExpense(): number {
      return this.filteredTransactions
        .filter((t: Transaction) => t.type === "expense")
        .reduce((sum: number, t: Transaction) => sum + Number(t.amount), 0);
    },

    currentBalance(): number {
      return this.totalIncome - this.totalExpense;
    },

    expensesByCategory(): Record<string, number> {
      const expenses = this.filteredTransactions.filter((t: Transaction) => t.type === "expense");
      return expenses.reduce(
        (acc: Record<string, number>, txn: Transaction) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        },
        {} as Record<string, number>,
      );
    },

    incomeByCategory(): Record<string, number> {
      const incomes = this.filteredTransactions.filter((t: Transaction) => t.type === "income");
      return incomes.reduce(
        (acc: Record<string, number>, txn: Transaction) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        },
        {} as Record<string, number>,
      );
    },

    recentTransactions(): Transaction[] {
      return this.filteredTransactions.slice(0, 5);
    },
  },
  actions: {
    async fetchTransactions() {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;

      this.isLoading = true;
      this.error = null;
      try {
        const data = await $fetch<{ transactions: Transaction[] }>(apiUrl);
        this.transactions = (data.transactions || []).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      } catch (err) {
        this.error = "Error loading transactions.";
      } finally {
        this.isLoading = false;
      }
    },
    async addTransaction(newTxn: Partial<Transaction>) {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;

      try {
        await $fetch(apiUrl, {
          method: "POST",
          body: newTxn,
        });
        await this.fetchTransactions();
      } catch (err) {
        throw new Error("Failed to add transaction");
      }
    },
  },
});
