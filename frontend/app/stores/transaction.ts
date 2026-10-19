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
      serverBalance: 0, // Driven entirely by DynamoDB Atomic Counter
      isLoading: false,
      error: null as string | null,
      selectedMonth: currentMonth,
    };
  },
  getters: {
    totalIncome(state): number {
      return state.transactions.filter((t: Transaction) => t.type === "income").reduce((sum: number, t: Transaction) => sum + Number(t.amount), 0);
    },
    totalExpense(state): number {
      return state.transactions.filter((t: Transaction) => t.type === "expense").reduce((sum: number, t: Transaction) => sum + Number(t.amount), 0);
    },
    expensesByCategory(state): Record<string, number> {
      const expenses = state.transactions.filter((t: Transaction) => t.type === "expense");
      return expenses.reduce(
        (acc: Record<string, number>, txn: Transaction) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        },
        {} as Record<string, number>,
      );
    },
    incomeByCategory(state): Record<string, number> {
      const incomes = state.transactions.filter((t: Transaction) => t.type === "income");
      return incomes.reduce(
        (acc: Record<string, number>, txn: Transaction) => {
          acc[txn.category] = (acc[txn.category] || 0) + Number(txn.amount);
          return acc;
        },
        {} as Record<string, number>,
      );
    },
    recentTransactions(state): Transaction[] {
      return state.transactions.slice(0, 5);
    },
  },
  actions: {
    async fetchTransactions() {
      const config = useRuntimeConfig();
      const apiUrl = config.public.apiUrl as string;

      this.isLoading = true;
      this.error = null;
      try {
        // Appends the ?month= query to make DynamoDB highly efficient
        const data = await $fetch<{ balance: number; transactions: Transaction[] }>(`${apiUrl}?month=${this.selectedMonth}`);

        this.serverBalance = data.balance || 0;
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
        await $fetch(apiUrl, { method: "POST", body: newTxn });
        await this.fetchTransactions(); // Fetches updated server balance immediately
      } catch (err) {
        throw new Error("Failed to add transaction");
      }
    },
  },
});
