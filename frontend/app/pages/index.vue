<template>
  <div class="space-y-8 pb-16">
    <!-- Header & Month Filter -->
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 tracking-tight">Financial Overview</h2>
        <p class="text-sm text-slate-500 font-medium mt-0.5">Track and analyze cash flow in real time</p>
      </div>

      <div class="relative w-full sm:w-auto">
        <select
          v-model="store.selectedMonth"
          class="w-full sm:w-auto appearance-none bg-slate-50 border border-slate-200 text-slate-700 font-semibold py-2.5 pl-4 pr-10 rounded-xl shadow-sm hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer transition-all">
          <option v-for="month in monthOptions" :key="month.value" :value="month.value">
            {{ month.label }}
          </option>
        </select>
        <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>
      </div>
    </div>

    <!-- Top Row: Summary KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs font-bold tracking-wider uppercase text-slate-400">Net Balance</span>
          <div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
        </div>
        <h3 class="text-3xl font-extrabold text-slate-900 tracking-tight">{{ formatRupiah(store.currentBalance) }}</h3>
      </div>

      <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs font-bold tracking-wider uppercase text-slate-400">Total Income</span>
          <div class="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
            </svg>
          </div>
        </div>
        <h3 class="text-3xl font-extrabold text-emerald-600 tracking-tight">+ {{ formatRupiah(store.totalIncome) }}</h3>
      </div>

      <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs font-bold tracking-wider uppercase text-slate-400">Total Expenses</span>
          <div class="p-2 bg-rose-50 text-rose-600 rounded-lg">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
            </svg>
          </div>
        </div>
        <h3 class="text-3xl font-extrabold text-rose-600 tracking-tight">- {{ formatRupiah(store.totalExpense) }}</h3>
      </div>
    </div>

    <!-- Full Width Quick Add Card -->
    <div class="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-xl border border-slate-800">
      <div class="flex items-center gap-2 mb-4">
        <div class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
        <h3 class="text-lg font-bold tracking-tight">Quick Add Transaction</h3>
      </div>

      <form @submit.prevent="submitTransaction" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Category</label>
          <input
            v-model="newTxn.category"
            type="text"
            required
            placeholder="e.g. Food, Salary"
            class="w-full bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Amount (Rp)</label>
          <input
            v-model="newTxn.amount"
            type="number"
            required
            placeholder="50000"
            class="w-full bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Type</label>
          <select
            v-model="newTxn.type"
            class="w-full bg-slate-800/80 border border-slate-700 text-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer transition-all">
            <option value="expense" class="bg-slate-900 text-white">Expense</option>
            <option value="income" class="bg-slate-900 text-white">Income</option>
          </select>
        </div>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-6 rounded-xl shadow-lg shadow-blue-600/30 active:scale-[0.98] disabled:opacity-50 transition-all cursor-pointer">
          {{ isSubmitting ? "Processing..." : "Add Transaction" }}
        </button>
      </form>
    </div>

    <!-- Analytics Row: Charts Side-by-Side -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <CategoryChart title="Expenses by Category" :categoryData="store.expensesByCategory" type="expense" />
      <CategoryChart title="Income by Category" :categoryData="store.incomeByCategory" type="income" />
    </div>

    <!-- Recent Transactions List -->
    <div class="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
        <h3 class="text-base font-bold text-slate-800">Recent Transactions ({{ currentMonthLabel }})</h3>
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top 5 Recent</span>
      </div>

      <div v-if="store.isLoading" class="p-8 text-center text-slate-400 font-medium">Loading transactions...</div>
      <div v-else-if="store.error" class="p-8 text-center text-rose-600 font-medium">{{ store.error }}</div>

      <ul v-else class="divide-y divide-slate-100">
        <TransactionCard v-for="txn in store.recentTransactions" :key="txn.SK" :txn="txn" />
        <li v-if="store.recentTransactions.length === 0" class="p-12 text-center text-slate-400 bg-white font-medium">
          No records found for {{ currentMonthLabel }}.
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from "vue";
  import { useTransactionStore } from "~/stores/transaction";
  import { useCurrency } from "~/composables/useCurrency";
  import CategoryChart from "~/components/CategoryChart.vue";

  const store = useTransactionStore();
  const { formatRupiah } = useCurrency();
  const isSubmitting = ref(false);

  const newTxn = ref({
    category: "",
    amount: null,
    type: "expense",
  });

  const monthOptions = computed(() => {
    const options = [];
    const date = new Date();
    for (let i = 0; i < 6; i++) {
      const d = new Date(date.getFullYear(), date.getMonth() - i, 1);
      const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      const label = d.toLocaleDateString("id-ID", { month: "long", year: "numeric" });
      options.push({ value, label });
    }
    return options;
  });

  const currentMonthLabel = computed(() => {
    const selected = monthOptions.value.find((m) => m.value === store.selectedMonth);
    return selected ? selected.label : "Selected Month";
  });

  onMounted(() => {
    store.fetchTransactions();
  });

  async function submitTransaction() {
    isSubmitting.value = true;
    try {
      const payload = { ...newTxn.value, timestamp: new Date().toISOString() };
      await store.addTransaction(payload);
      newTxn.value = { category: "", amount: null, type: "expense" };
    } catch (err) {
      alert("Failed to add transaction");
    } finally {
      isSubmitting.value = false;
    }
  }
</script>
