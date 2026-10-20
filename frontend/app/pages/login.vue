<template>
  <div class="min-h-[80vh] flex items-center justify-center bg-brokenwhite py-12">
    <div class="bg-white p-8 rounded-2xl shadow-lg border border-darkpurple/5 w-full max-w-md">
      <div class="flex items-center justify-center gap-2 mb-8">
        <div class="w-4 h-4 rounded-full bg-darkpurple"></div>
        <h1 class="text-2xl font-extrabold tracking-tight text-darkpurple-dark">Financial Tracker</h1>
      </div>

      <!-- ERROR MESSAGE -->
      <div v-if="errorMessage" class="mb-6 p-3 bg-rose-50 text-rose-600 text-sm font-bold rounded-xl text-center border border-rose-100">
        {{ errorMessage }}
      </div>

      <!-- LOGIN / REGISTER FORM -->
      <form v-if="viewState === 'login' || viewState === 'register'" @submit.prevent="handleAuth" class="space-y-5">
        <h2 class="text-xl font-bold text-center text-darkpurple-dark mb-6">
          {{ viewState === "login" ? "Sign in to your account" : "Create a new account" }}
        </h2>

        <!-- NAME (Only for Register) -->
        <div v-if="viewState === 'register'">
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Full Name</label>
          <input
            v-model="fullName"
            type="text"
            required
            placeholder="John Doe"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-3 focus:ring-2 focus:ring-darkpurple focus:outline-none transition-all" />
        </div>

        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Email Address</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="you@example.com"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-3 focus:ring-2 focus:ring-darkpurple focus:outline-none transition-all" />
        </div>

        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Password</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="••••••••"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-3 focus:ring-2 focus:ring-darkpurple focus:outline-none transition-all" />
          <p v-if="viewState === 'register'" class="text-[10px] text-darkpurple-light mt-1.5">
            Requires 8+ characters, numbers, uppercase, and symbols.
          </p>
        </div>

        <!-- CONFIRM PASSWORD (Only for Register) -->
        <div v-if="viewState === 'register'">
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Confirm Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            placeholder="••••••••"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-3 focus:ring-2 focus:ring-darkpurple focus:outline-none transition-all" />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-darkpurple hover:bg-darkpurple-light text-white font-bold py-3 px-6 rounded-xl shadow-lg shadow-darkpurple/20 transition-all mt-4 disabled:opacity-50">
          {{ isLoading ? "Processing..." : viewState === "login" ? "Sign In" : "Create Account" }}
        </button>

        <p class="text-center text-sm text-darkpurple-light font-medium mt-4">
          {{ viewState === "login" ? "Don't have an account?" : "Already have an account?" }}
          <button type="button" @click="toggleView" class="text-darkpurple hover:underline font-bold">
            {{ viewState === "login" ? "Sign Up" : "Log In" }}
          </button>
        </p>
      </form>

      <!-- VERIFY OTP FORM -->
      <form v-if="viewState === 'verify'" @submit.prevent="handleVerify" class="space-y-5">
        <h2 class="text-xl font-bold text-center text-darkpurple-dark mb-2">Verify Your Email</h2>
        <p class="text-sm text-center text-darkpurple-light mb-6">
          We sent a verification code to
          <br />
          <span class="font-bold text-darkpurple">{{ email }}</span>
        </p>

        <div>
          <label class="block text-xs font-bold text-darkpurple-light uppercase tracking-wider mb-1.5">Verification Code</label>
          <input
            v-model="code"
            type="text"
            required
            placeholder="Enter the 6-digit code"
            class="w-full bg-brokenwhite border border-darkpurple/20 text-darkpurple-dark rounded-xl px-4 py-3 focus:ring-2 focus:ring-darkpurple focus:outline-none transition-all text-center tracking-widest font-bold" />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg shadow-emerald-600/20 transition-all mt-4 disabled:opacity-50">
          {{ isLoading ? "Verifying..." : "Verify Email" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
  import { ref } from "vue";
  import { useRouter } from "vue-router";
  import { useCognito } from "~/composables/useCognito";
  import { useAuthStore } from "~/stores/auth";

  const router = useRouter();
  const { registerUser, loginUser, verifyEmail } = useCognito();
  const authStore = useAuthStore();

  const viewState = ref("login");
  const isLoading = ref(false);
  const errorMessage = ref("");

  const fullName = ref("");
  const email = ref("");
  const password = ref("");
  const confirmPassword = ref("");
  const code = ref("");

  // NEW: Store the internal Cognito username temporarily during the session
  const actualUsername = ref("");

  function toggleView() {
    errorMessage.value = "";
    viewState.value = viewState.value === "login" ? "register" : "login";
  }

  async function handleAuth() {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      if (viewState.value === "register") {
        if (password.value !== confirmPassword.value) {
          throw new Error("Passwords do not match.");
        }

        // 1. Capture the user object returned from AWS
        const cognitoUser = await registerUser(email.value, password.value, fullName.value);

        // 2. Save the internal username (e.g., 'user_x8f9a') to memory
        actualUsername.value = cognitoUser.getUsername();

        viewState.value = "verify";
      } else {
        const token = await loginUser(email.value, password.value);
        authStore.setToken(token);
        router.push("/");
      }
    } catch (error) {
      errorMessage.value = error.message || error;
    } finally {
      isLoading.value = false;
    }
  }

  async function handleVerify() {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      // 3. Verify using the internal username, NOT the email
      await verifyEmail(actualUsername.value, code.value);

      // 4. Log in using the email alias (Cognito allows this for login)
      const token = await loginUser(email.value, password.value);
      localStorage.setItem("auth_token", token);

      router.push("/");
    } catch (error) {
      errorMessage.value = error.message || error;
    } finally {
      isLoading.value = false;
    }
  }
</script>
