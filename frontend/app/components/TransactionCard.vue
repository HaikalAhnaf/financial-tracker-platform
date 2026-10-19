<template>
  <li class="p-6 flex justify-between items-center hover:bg-gray-50">
    <div>
      <p class="text-sm font-medium text-gray-900">{{ txn.category }}</p>
      <p class="text-xs text-gray-500">{{ new Date(txn.timestamp).toLocaleDateString("id-ID") }}</p>
    </div>
    <div :class="txn.type === 'expense' ? 'text-red-600' : 'text-green-600'" class="font-bold text-lg">
      {{ txn.type === "expense" ? "-" : "+" }} {{ formatRupiah(txn.amount) }}
    </div>
  </li>
</template>

<script setup>
  // Receive the transaction object from the parent page
  defineProps(["txn"]);
  // Auto-imported composable
  const { formatRupiah } = useCurrency();
</script>
