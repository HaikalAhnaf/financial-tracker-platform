<template>
  <div>
    <!-- Form -->
    <div class="bg-white rounded-xl shadow p-6 mb-8">
      <form @submit.prevent="submitTransaction" class="flex gap-4 items-end">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
          <input
            v-model="newTxn.category"
            type="text"
            required
            placeholder="e.g. Internet Bill"
            class="w-full border-gray-300 rounded-md shadow-sm p-2 border" />
        </div>
        <div class="w-40">
          <label class="block text-sm font-medium text-gray-700 mb-1">Amount (Rp)</label>
          <input v-model="newTxn.amount" type="number" required placeholder="50000" class="w-full border-gray-300 rounded-md shadow-sm p-2 border" />
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

    <!-- Data States -->
    <div v-if="store.isLoading" class="text-gray-500 mb-4">Loading your data...</div>
    <div v-else-if="store.error" class="bg-red-100 text-red-700 p-4 rounded mb-4">{{ store.error }}</div>

    <!-- Transaction List (Using our component!) -->
    <div v-else class="bg-white rounded-xl shadow overflow-hidden">
      <ul class="divide-y divide-gray-200">
        <TransactionCard v-for="txn in store.transactions" :key="txn.SK" :txn="txn" />
      </ul>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from "vue";
  import { useTransactionStore } from "~/stores/transaction";

  const store = useTransactionStore();
  const isSubmitting = ref(false);

  const newTxn = ref({
    category: "",
    amount: null,
    type: "expense",
  });

  // Fetch data when page loads
  onMounted(() => {
    store.fetchTransactions();
  });

  async function submitTransaction() {
    isSubmitting.value = true;
    try {
      await store.addTransaction(newTxn.value);
      newTxn.value = { category: "", amount: null, type: "expense" }; // Reset form
    } catch (err) {
      alert("Failed to add transaction");
    } finally {
      isSubmitting.value = false;
    }
  }
</script>
