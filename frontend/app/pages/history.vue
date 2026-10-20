<template>
  <div class="space-y-8 pb-16">
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5">
      <div>
        <h2 class="text-2xl font-bold text-darkpurple-dark tracking-tight">Transaction Ledger</h2>
        <p class="text-sm text-darkpurple-light font-medium mt-0.5">Comprehensive view of your financial history</p>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
        <button
          @click="exportToXLSX"
          :disabled="filteredTransactions.length === 0"
          class="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-xl shadow-sm transition-all disabled:opacity-50 cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Export XLSX
        </button>

        <div class="relative">
          <select
            v-model="store.historyRange"
            class="w-full sm:w-auto appearance-none bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark font-bold py-2.5 pl-4 pr-10 rounded-xl hover:border-darkpurple/40 focus:outline-none focus:ring-2 focus:ring-darkpurple/20 transition-all cursor-pointer">
            <option value="3m">Last 3 Months</option>
            <option value="6m">Last 6 Months</option>
            <option value="1y">Last 1 Year</option>
            <option value="all">All Time</option>
          </select>
          <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-darkpurple-light">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white p-4 rounded-2xl shadow-sm border border-darkpurple/5 flex flex-col md:flex-row justify-between items-center gap-4">
      <div class="relative w-full md:w-80">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search category or note..."
          class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark placeholder-darkpurple-light/60 rounded-xl pl-10 pr-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none text-sm transition-all" />
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-darkpurple-light">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>

      <div class="flex items-center gap-2 w-full md:w-auto justify-start md:justify-end">
        <button
          @click="typeFilter = 'all'"
          :class="typeFilter === 'all' ? 'bg-darkpurple text-white shadow-md' : 'bg-brokenwhite text-darkpurple-light hover:bg-darkpurple/10'"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer">
          All
        </button>
        <button
          @click="typeFilter = 'income'"
          :class="
            typeFilter === 'income'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'bg-brokenwhite text-darkpurple-light hover:bg-emerald-50 hover:text-emerald-600'
          "
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer">
          Income
        </button>
        <button
          @click="typeFilter = 'expense'"
          :class="
            typeFilter === 'expense'
              ? 'bg-rose-600 text-white shadow-md'
              : 'bg-brokenwhite text-darkpurple-light hover:bg-rose-50 hover:text-rose-600'
          "
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer">
          Expense
        </button>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-sm border border-darkpurple/10 overflow-hidden">
      <div v-if="store.isLoading" class="p-12 text-center text-darkpurple-light font-medium">Loading ledger data...</div>
      <div v-else-if="store.error" class="p-12 text-center text-rose-600 font-medium">{{ store.error }}</div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-darkpurple text-white">
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider">Date</th>
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider">Category</th>
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider">Type</th>
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider text-right">Amount</th>
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider">Note</th>
              <th class="py-4 px-6 text-xs font-bold uppercase tracking-wider text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-darkpurple/5 bg-white">
            <tr v-for="txn in filteredTransactions" :key="txn.SK" class="hover:bg-brokenwhite/60 transition-colors group">
              <td class="py-4 px-6 text-sm font-medium text-darkpurple-dark whitespace-nowrap">
                {{ new Date(txn.timestamp).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) }}
              </td>
              <td class="py-4 px-6 text-sm text-darkpurple-dark font-semibold">{{ txn.category }}</td>
              <td class="py-4 px-6">
                <span
                  :class="txn.type === 'income' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
                  class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide inline-block">
                  {{ txn.type }}
                </span>
              </td>
              <td
                class="py-4 px-6 text-sm font-bold text-right whitespace-nowrap"
                :class="txn.type === 'income' ? 'text-emerald-600' : 'text-rose-600'">
                {{ txn.type === "income" ? "+" : "-" }} {{ formatRupiah(txn.amount) }}
              </td>

              <!-- Editable Note Column -->
              <td class="py-4 px-6 text-sm text-darkpurple-light">
                <div v-if="editingNoteSk === txn.SK" class="flex items-center gap-2">
                  <input
                    v-model="tempNote"
                    type="text"
                    class="w-full min-w-[120px] bg-brokenwhite border border-darkpurple/20 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-darkpurple text-xs" />
                  <button @click="saveNote(txn.SK)" :disabled="isSavingNote" class="text-emerald-600 hover:text-emerald-700 font-bold text-xs">
                    Save
                  </button>
                  <button @click="editingNoteSk = null" class="text-darkpurple-light hover:text-rose-600 font-bold text-xs">Cancel</button>
                </div>
                <div v-else class="flex items-center justify-between group/note">
                  <span>{{ txn.note || "-" }}</span>
                  <button
                    @click="startEditNote(txn)"
                    class="opacity-0 group-hover/note:opacity-100 text-darkpurple-light hover:text-darkpurple transition-opacity p-1"
                    title="Edit Note">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                    </svg>
                  </button>
                </div>
              </td>

              <td class="py-4 px-6 text-center">
                <button
                  @click="handleDelete(txn.SK)"
                  :disabled="isDeleting === txn.SK"
                  class="text-darkpurple-light hover:text-rose-600 transition-colors disabled:opacity-50 p-1"
                  title="Delete transaction">
                  <svg v-if="isDeleting !== txn.SK" class="w-5 h-5 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                  <span v-else class="text-xs font-bold text-rose-600">...</span>
                </button>
              </td>
            </tr>
            <tr v-if="filteredTransactions.length === 0">
              <td colspan="6" class="py-12 text-center text-darkpurple-light font-medium bg-white">No matching transactions found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from "vue";
  import { useTransactionStore } from "~/stores/transaction";
  import { useCurrency } from "~/composables/useCurrency";
  import * as XLSX from "xlsx";

  const store = useTransactionStore();
  const { formatRupiah } = useCurrency();
  const isDeleting = ref(null);

  const searchQuery = ref("");
  const typeFilter = ref("all");

  // Inline Note Edit State
  const editingNoteSk = ref(null);
  const tempNote = ref("");
  const isSavingNote = ref(false);

  const filteredTransactions = computed(() => {
    return store.historyTransactions.filter((txn) => {
      const matchesType = typeFilter.value === "all" || txn.type === typeFilter.value;
      // Search now checks both category and note
      const searchString = `${txn.category} ${txn.note || ""}`.toLowerCase();
      const matchesSearch = searchString.includes(searchQuery.value.toLowerCase().trim());
      return matchesType && matchesSearch;
    });
  });

  watch(
    () => store.historyRange,
    () => {
      store.fetchHistory();
    },
  );

  onMounted(() => {
    store.fetchHistory();
  });

  function startEditNote(txn) {
    editingNoteSk.value = txn.SK;
    tempNote.value = txn.note || "";
  }

  async function saveNote(sk) {
    isSavingNote.value = true;
    try {
      await store.updateNote(sk, tempNote.value);
      editingNoteSk.value = null;
    } catch (err) {
      alert("Failed to update note");
    } finally {
      isSavingNote.value = false;
    }
  }

  async function handleDelete(sk) {
    if (!confirm("Are you sure you want to delete this transaction? Your balance will be automatically adjusted.")) return;
    isDeleting.value = sk;
    try {
      await store.deleteTransaction(sk);
    } catch (error) {
      alert("Failed to delete transaction.");
    } finally {
      isDeleting.value = null;
    }
  }

  function exportToXLSX() {
    if (filteredTransactions.value.length === 0) return;

    const exportData = filteredTransactions.value.map((txn) => ({
      // Force English format for the Excel export
      Date: new Date(txn.timestamp).toLocaleDateString("en-US"),
      Category: txn.category,
      Type: txn.type.toUpperCase(),
      "Amount (Rp)": Number(txn.amount),
      Note: txn.note || "",
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Financial History");

    const dateStr = new Date().toISOString().split("T")[0];
    XLSX.writeFile(workbook, `Financial_History_${dateStr}.xlsx`);
  }
</script>
