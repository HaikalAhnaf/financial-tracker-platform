<template>
  <div class="min-h-screen bg-gray-100 p-8 font-sans">
    <div class="max-w-2xl mx-auto">
      <h1 class="text-3xl font-bold text-gray-800 mb-8">Cloud Financial Tracker</h1>

      <!-- Transaction Input Form -->
      <div class="bg-white rounded-xl shadow p-6 mb-8">
        <form @submit.prevent="addTransaction" class="flex gap-4 items-end">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <input
              v-model="newTxn.category"
              type="text"
              required
              placeholder="e.g. Internet Bill"
              class="w-full border-gray-300 rounded-md shadow-sm p-2 border" />
          </div>
          <div class="w-32">
            <label class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
            <input
              v-model="newTxn.amount"
              type="number"
              step="0.01"
              required
              placeholder="0.00"
              class="w-full border-gray-300 rounded-md shadow-sm p-2 border" />
          </div>
          <div class="w-32">
            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select v-model="newTxn.type" class="w-full border-gray-300 rounded-md shadow-sm p-2 border">
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>
          <button type="submit" :disabled="isSubmitting" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">
            {{ isSubmitting ? "Adding..." : "Add" }}
          </button>
        </form>
      </div>

      <!-- Transaction List -->
      <div v-if="pending" class="text-gray-500 mb-4">Loading your data...</div>
      <div v-else-if="error" class="bg-red-100 text-red-700 p-4 rounded mb-4">Error loading transactions.</div>

      <div v-else class="bg-white rounded-xl shadow overflow-hidden">
        <ul class="divide-y divide-gray-200">
          <li v-for="txn in transactions" :key="txn.SK" class="p-6 flex justify-between items-center hover:bg-gray-50">
            <div>
              <p class="text-sm font-medium text-gray-900">{{ txn.category }}</p>
              <p class="text-xs text-gray-500">{{ new Date(txn.timestamp).toLocaleDateString() }}</p>
            </div>
            <div :class="txn.type === 'expense' ? 'text-red-600' : 'text-green-600'" class="font-bold text-lg">
              {{ txn.type === "expense" ? "-" : "+" }}${{ txn.amount }}
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed } from "vue";

  const apiUrl = "https://sf2bukjp9b.execute-api.ap-southeast-1.amazonaws.com";
  const { data, pending, error, refresh } = await useFetch(apiUrl);

  const transactions = computed(() => {
    // Sort transactions by newest first
    const txns = data.value?.transactions || [];
    return txns.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  });

  const isSubmitting = ref(false);
  const newTxn = ref({
    category: "",
    amount: null,
    type: "expense",
  });

  async function addTransaction() {
    isSubmitting.value = true;
    try {
      await $fetch(apiUrl, {
        method: "POST",
        body: newTxn.value,
      });

      // Reset form and refresh data from AWS
      newTxn.value = { category: "", amount: null, type: "expense" };
      await refresh();
    } catch (err) {
      alert("Failed to add transaction");
    } finally {
      isSubmitting.value = false;
    }
  }
</script>
