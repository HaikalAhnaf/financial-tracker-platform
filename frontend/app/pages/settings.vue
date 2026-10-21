<template>
  <div class="space-y-8 pb-16">
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5">
      <div>
        <h2 class="text-2xl font-bold text-darkpurple-dark tracking-tight">Account Settings</h2>
        <p class="text-sm text-darkpurple-light font-medium mt-0.5">Manage profile, security, categories, and automated reports</p>
      </div>
    </div>

    <!-- 2-COLUMN BALANCED GRID -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      <!-- LEFT COLUMN: Profile & Security -->
      <div class="space-y-8">
        <!-- Profile Info -->
        <div class="bg-white rounded-2xl p-8 shadow-sm border border-darkpurple/10">
          <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark mb-6">Profile Information</h3>
          <div class="space-y-6">
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Full Name</label>
              <input
                type="text"
                disabled
                :value="authStore.user?.name"
                class="w-full bg-brokenwhite border border-darkpurple/10 text-darkpurple-dark rounded-xl px-4 py-3 opacity-70 cursor-not-allowed font-semibold" />
            </div>
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Registered Email</label>
              <input
                type="email"
                disabled
                :value="authStore.user?.email"
                class="w-full bg-brokenwhite border border-darkpurple/10 text-darkpurple-dark rounded-xl px-4 py-3 opacity-70 cursor-not-allowed font-semibold" />
            </div>
          </div>
        </div>

        <!-- Security & Password Reset -->
        <div class="bg-white rounded-2xl p-8 shadow-sm border border-darkpurple/10">
          <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark mb-6">Security</h3>

          <div v-if="resetSuccess" class="p-4 bg-emerald-50 text-emerald-700 font-bold rounded-xl mb-4 text-sm border border-emerald-100">
            Password successfully updated!
          </div>
          <div v-if="resetError" class="p-4 bg-rose-50 text-rose-700 font-bold rounded-xl mb-4 text-sm border border-rose-100">
            {{ resetError }}
          </div>

          <div v-if="resetState === 'idle'">
            <p class="text-sm text-darkpurple-light mb-6">Require a password change? We will send a verification code to your registered email.</p>
            <button
              @click="initiatePasswordReset"
              :disabled="isResetting"
              class="bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-2.5 px-6 rounded-xl shadow-lg shadow-darkpurple/20 transition-all disabled:opacity-50">
              {{ isResetting ? "Sending Code..." : "Reset Password" }}
            </button>
          </div>

          <form v-if="resetState === 'awaiting_otp'" @submit.prevent="confirmPassword" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Verification Code</label>
              <input
                v-model="resetOtp"
                type="text"
                required
                placeholder="6-digit code"
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none" />
            </div>
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">New Password</label>
              <input
                v-model="newPassword"
                type="password"
                required
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none" />
            </div>
            <div class="flex gap-3 pt-2">
              <button
                type="submit"
                :disabled="isResetting"
                class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-6 rounded-xl transition-all disabled:opacity-50">
                {{ isResetting ? "Saving..." : "Confirm New Password" }}
              </button>
              <button
                type="button"
                @click="resetState = 'idle'"
                class="bg-brokenwhite text-darkpurple-light font-bold py-2.5 px-6 rounded-xl transition-all">
                Cancel
              </button>
            </div>
          </form>

          <div class="mt-8 pt-8 border-t border-darkpurple/10">
            <button
              @click="authStore.logout"
              class="bg-rose-50 text-rose-600 hover:bg-rose-100 font-bold py-2.5 px-6 rounded-xl transition-all border border-rose-200">
              Sign Out Securely
            </button>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: Reports & Categories -->
      <div class="space-y-8">
        <!-- Automated Monthly Reports -->
        <div class="bg-white rounded-2xl p-8 shadow-sm border border-darkpurple/10">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark">Automated Monthly Reports</h3>
              <p class="text-xs text-darkpurple-light mt-0.5">Scheduled via AWS EventBridge for 11:59 PM on the last day of each month.</p>
            </div>

            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="reportsEnabled" class="sr-only peer" />
              <div
                class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-darkpurple"></div>
            </label>
          </div>

          <div
            v-if="reportStatusMsg"
            :class="reportStatusIsError ? 'bg-rose-50 text-rose-700 border-rose-100' : 'bg-emerald-50 text-emerald-700 border-emerald-100'"
            class="p-3 text-xs font-bold rounded-xl mb-4 border text-center">
            {{ reportStatusMsg }}
          </div>

          <div class="grid grid-cols-2 gap-4 mb-6 border-t border-darkpurple/10 pt-4">
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Monthly Expense Limit (Rp)</label>
              <input
                v-model="budgetLimit"
                type="number"
                placeholder="e.g. 5000000"
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple outline-none" />
            </div>
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Alert Alarm Threshold (Rp)</label>
              <input
                v-model="budgetThreshold"
                type="number"
                placeholder="e.g. 250000"
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple outline-none" />
            </div>
          </div>

          <div class="space-y-4 pt-2">
            <div>
              <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Recipient Email List</label>

              <div class="flex gap-2 mb-3">
                <input
                  v-model="emailInput"
                  type="email"
                  placeholder="Add email recipient..."
                  class="flex-1 bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-darkpurple focus:outline-none" />
                <button
                  type="button"
                  @click="addRecipient"
                  class="bg-darkpurple hover:bg-darkpurple-light text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all">
                  Add
                </button>
              </div>

              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(email, idx) in reportEmails"
                  :key="idx"
                  class="inline-flex items-center gap-1.5 bg-brokenwhite border border-darkpurple/10 px-3 py-1.5 rounded-lg text-xs font-semibold text-darkpurple-dark">
                  {{ email }}
                  <button @click="removeRecipient(idx)" class="text-rose-500 hover:text-rose-700 font-bold ml-1">×</button>
                </span>
                <span v-if="reportEmails.length === 0" class="text-xs text-darkpurple-light/70 italic">
                  No recipients added yet. Your registered email will be used by default.
                </span>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row gap-3 pt-4 border-t border-darkpurple/10">
              <button
                @click="saveReportSettings"
                :disabled="isSavingSettings"
                class="flex-1 bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-2.5 px-4 rounded-xl text-xs shadow-md shadow-darkpurple/20 transition-all disabled:opacity-50">
                {{ isSavingSettings ? "Saving..." : "Save Settings" }}
              </button>

              <button
                @click="triggerManualReport"
                :disabled="isSendingReport"
                class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 flex items-center justify-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
                {{ isSendingReport ? "Sending..." : "Send Report Now" }}
              </button>
            </div>
          </div>
        </div>

        <!-- Manage Categories -->
        <div class="bg-white rounded-2xl p-8 shadow-sm border border-darkpurple/10">
          <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark mb-6">Manage Categories</h3>

          <form @submit.prevent="submitCategory" class="flex flex-col sm:flex-row gap-3 mb-8">
            <div class="flex-1">
              <input
                v-model="newCatName"
                type="text"
                required
                placeholder="New category name"
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none" />
            </div>
            <div class="w-full sm:w-40">
              <select
                v-model="newCatType"
                class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-darkpurple focus:outline-none cursor-pointer">
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <button
              type="submit"
              :disabled="categoryStore.isLoading"
              class="bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-2.5 px-6 rounded-xl transition-all disabled:opacity-50">
              Add
            </button>
          </form>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-4 border-b border-darkpurple/10 pb-2">
                Expense Categories
              </h4>
              <ul class="space-y-2">
                <li
                  v-for="cat in categoryStore.expenseCategories"
                  :key="cat.SK"
                  class="flex justify-between items-center group bg-brokenwhite/50 px-3 py-2 rounded-lg border border-darkpurple/5">
                  <span class="text-sm font-semibold text-darkpurple-dark">{{ cat.name }}</span>
                  <button
                    @click="deleteCat(cat.SK)"
                    class="text-rose-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </li>
              </ul>
            </div>

            <div>
              <h4 class="text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-4 border-b border-darkpurple/10 pb-2">
                Income Categories
              </h4>
              <ul class="space-y-2">
                <li
                  v-for="cat in categoryStore.incomeCategories"
                  :key="cat.SK"
                  class="flex justify-between items-center group bg-brokenwhite/50 px-3 py-2 rounded-lg border border-darkpurple/5">
                  <span class="text-sm font-semibold text-darkpurple-dark">{{ cat.name }}</span>
                  <button
                    @click="deleteCat(cat.SK)"
                    class="text-rose-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from "vue";
  import { useAuthStore } from "~/stores/auth";
  import { useCategoryStore } from "~/stores/category";
  import { useCognito } from "~/composables/useCognito";

  const config = useRuntimeConfig();
  const authStore = useAuthStore();
  const categoryStore = useCategoryStore();
  const { resetPassword, confirmPasswordReset } = useCognito();

  // Category State
  const newCatName = ref("");
  const newCatType = ref("expense");

  // Password Reset State
  const resetState = ref("idle");
  const isResetting = ref(false);
  const resetError = ref("");
  const resetSuccess = ref(false);
  const resetOtp = ref("");
  const newPassword = ref("");

  // Automated Report State
  const reportsEnabled = ref(false);
  const reportEmails = ref([]);
  const emailInput = ref("");
  const isSavingSettings = ref(false);
  const isSendingReport = ref(false);
  const reportStatusMsg = ref("");
  const reportStatusIsError = ref(false);

  // Budget limit
  const budgetLimit = ref("");
  const budgetThreshold = ref("");

  onMounted(() => {
    categoryStore.fetchCategories();
    fetchReportSettings();
  });

  async function fetchReportSettings() {
    try {
      const data = await $fetch(`${config.public.apiUrl}?entity=settings`, {
        headers: { Authorization: `Bearer ${authStore.token}` },
      });
      if (data?.settings) {
        reportsEnabled.value = !!data.settings.reports_enabled;
        reportEmails.value = data.settings.report_emails || [];
        budgetLimit.value = data.settings.budget_limit || "";
        budgetThreshold.value = data.settings.budget_threshold || "";
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  }

  function addRecipient() {
    const val = emailInput.value.trim().toLowerCase();
    if (val && !reportEmails.value.includes(val)) {
      reportEmails.value.push(val);
      emailInput.value = "";
    }
  }

  function removeRecipient(idx) {
    reportEmails.value.splice(idx, 1);
  }

  async function saveReportSettings() {
    isSavingSettings.value = true;
    reportStatusMsg.value = "";
    reportStatusIsError.value = false;

    try {
      await $fetch(`${config.public.apiUrl}?entity=settings`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authStore.token}` },
        body: {
          reports_enabled: reportsEnabled.value,
          report_emails: reportEmails.value,
          budget_limit: Number(budgetLimit.value),
          budget_threshold: Number(budgetThreshold.value),
        },
      });
      reportStatusMsg.value = "Report settings saved!";
    } catch (err) {
      reportStatusIsError.value = true;
      reportStatusMsg.value = "Failed to save settings.";
    } finally {
      isSavingSettings.value = false;
    }
  }

  async function triggerManualReport() {
    isSendingReport.value = true;
    reportStatusMsg.value = "";
    reportStatusIsError.value = false;

    try {
      const res = await $fetch(`${config.public.apiUrl}?entity=report`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authStore.token}` },
      });
      reportStatusMsg.value = res.message || "Report sent successfully!";
    } catch (err) {
      reportStatusIsError.value = true;
      reportStatusMsg.value = err.data?.details || err.data?.error || "Failed to send report.";
    } finally {
      isSendingReport.value = false;
    }
  }

  async function submitCategory() {
    if (!newCatName.value) return;
    try {
      await categoryStore.addCategory(newCatName.value, newCatType.value);
      newCatName.value = "";
    } catch (err) {
      alert("Failed to add category");
    }
  }

  async function deleteCat(sk) {
    if (!confirm("Delete this category?")) return;
    try {
      await categoryStore.deleteCategory(sk);
    } catch (err) {
      alert("Failed to delete category");
    }
  }

  async function initiatePasswordReset() {
    isResetting.value = true;
    resetError.value = "";
    resetSuccess.value = false;
    try {
      await resetPassword(authStore.user.email);
      resetState.value = "awaiting_otp";
    } catch (error) {
      resetError.value = error;
    } finally {
      isResetting.value = false;
    }
  }

  async function confirmPassword() {
    isResetting.value = true;
    resetError.value = "";
    try {
      await confirmPasswordReset(authStore.user.email, resetOtp.value, newPassword.value);
      resetState.value = "idle";
      resetSuccess.value = true;
      resetOtp.value = "";
      newPassword.value = "";
    } catch (error) {
      resetError.value = error;
    } finally {
      isResetting.value = false;
    }
  }
</script>
