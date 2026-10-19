<template>
  <div class="space-y-8 pb-16">
    <!-- Header & Dynamic Month Filter -->
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5">
      <div>
        <h2 class="text-2xl font-bold text-darkpurple-dark tracking-tight">Dashboard Overview</h2>
        <p class="text-sm text-darkpurple-light font-medium mt-0.5">Track and analyze cash flow</p>
      </div>

      <div class="relative w-full sm:w-auto">
        <select
          v-model="store.selectedMonth"
          class="w-full sm:w-auto appearance-none bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark font-bold py-2.5 pl-4 pr-10 rounded-xl hover:border-darkpurple/40 focus:outline-none focus:ring-2 focus:ring-darkpurple/20 transition-all cursor-pointer">
          <option v-for="month in monthOptions" :key="month.value" :value="month.value">
            {{ month.label }}
          </option>
        </select>
        <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-darkpurple-light">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>
      </div>
    </div>

    <!-- Summary KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Total Account Balance (Driven by Backend) -->
      <div class="bg-darkpurple p-6 rounded-2xl shadow-lg relative overflow-hidden">
        <div class="absolute -right-4 -top-4 w-24 h-24 bg-white/5 rounded-full blur-2xl"></div>
        <span class="text-xs font-bold tracking-wider uppercase text-white/60 mb-2 block">Total Account Balance</span>
        <h3 class="text-3xl font-extrabold text-white tracking-tight">{{ formatRupiah(store.serverBalance) }}</h3>
      </div>

      <div class="bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5 hover:border-darkpurple/20 transition-colors">
        <span class="text-xs font-bold tracking-wider uppercase text-darkpurple-light mb-2 block">{{ currentMonthLabel }} Income</span>
        <h3 class="text-3xl font-extrabold text-emerald-600 tracking-tight">+ {{ formatRupiah(store.totalIncome) }}</h3>
      </div>

      <div class="bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5 hover:border-darkpurple/20 transition-colors">
        <span class="text-xs font-bold tracking-wider uppercase text-darkpurple-light mb-2 block">{{ currentMonthLabel }} Expenses</span>
        <h3 class="text-3xl font-extrabold text-rose-600 tracking-tight">- {{ formatRupiah(store.totalExpense) }}</h3>
      </div>
    </div>

    <!-- Quick Add Form -->
    <div class="bg-white rounded-2xl p-6 shadow-sm border border-darkpurple/10">
      <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark mb-4">Quick Add Transaction</h3>

      <form @submit.prevent="submitTransaction" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Category</label>
          <input
            v-model="newTxn.category"
            type="text"
            required
            placeholder="e.g. Food"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none" />
        </div>
        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Amount (Rp)</label>
          <input
            v-model="newTxn.amount"
            type="number"
            required
            placeholder="50000"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none" />
        </div>
        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Type</label>
          <select
            v-model="newTxn.type"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none cursor-pointer">
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </div>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-2.5 px-6 rounded-xl shadow-lg shadow-darkpurple/20 transition-all">
          {{ isSubmitting ? "Processing..." : "Add Transaction" }}
        </button>
      </form>
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <CategoryChart title="Expenses by Category" :categoryData="store.expensesByCategory" type="expense" />
      <CategoryChart title="Income by Category" :categoryData="store.incomeByCategory" type="income" />
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from "vue";
  import { useTransactionStore } from "~/stores/transaction";
  import { useCurrency } from "~/composables/useCurrency";
  import CategoryChart from "~/components/CategoryChart.vue";

  const store = useTransactionStore();
  const { formatRupiah } = useCurrency();
  const isSubmitting = ref(false);

  const newTxn = ref({ category: "", amount: null, type: "expense" });

  // Auto-trigger API fetch when the user changes the month dropdown
  watch(
    () => store.selectedMonth,
    () => {
      store.fetchTransactions();
    },
  );

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
