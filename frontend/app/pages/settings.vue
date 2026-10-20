<template>
  <div class="space-y-8 pb-16">
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-darkpurple/5">
      <div>
        <h2 class="text-2xl font-bold text-darkpurple-dark tracking-tight">Account Settings</h2>
        <p class="text-sm text-darkpurple-light font-medium mt-0.5">Manage your profile, categories, and security</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
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

          <!-- Step 1: Request OTP -->
          <div v-if="resetState === 'idle'">
            <p class="text-sm text-darkpurple-light mb-6">Require a password change? We will send a verification code to your registered email.</p>
            <button
              @click="initiatePasswordReset"
              :disabled="isResetting"
              class="bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-2.5 px-6 rounded-xl shadow-lg shadow-darkpurple/20 transition-all disabled:opacity-50">
              {{ isResetting ? "Sending Code..." : "Reset Password" }}
            </button>
          </div>

          <!-- Step 2: Confirm OTP and New Password -->
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

      <!-- RIGHT COLUMN: Category Management -->
      <div class="bg-white rounded-2xl p-8 shadow-sm border border-darkpurple/10 h-fit">
        <h3 class="text-lg font-bold tracking-tight text-darkpurple-dark mb-6">Manage Categories</h3>

        <!-- Add Category Form -->
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

        <!-- Category Lists -->
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
                <button @click="deleteCat(cat.SK)" class="text-rose-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
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
                <button @click="deleteCat(cat.SK)" class="text-rose-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
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
</template>

<script setup>
  import { ref, onMounted } from "vue";
  import { useAuthStore } from "~/stores/auth";
  import { useCategoryStore } from "~/stores/category";
  import { useCognito } from "~/composables/useCognito";

  const authStore = useAuthStore();
  const categoryStore = useCategoryStore();
  const { resetPassword, confirmPasswordReset } = useCognito();

  // Category State
  const newCatName = ref("");
  const newCatType = ref("expense");

  // Password Reset State
  const resetState = ref("idle"); // 'idle' | 'awaiting_otp'
  const isResetting = ref(false);
  const resetError = ref("");
  const resetSuccess = ref(false);
  const resetOtp = ref("");
  const newPassword = ref("");

  onMounted(() => {
    categoryStore.fetchCategories();
  });

  // Category Handlers
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

  // Password Reset Handlers
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
