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
      <div v-if="viewState === 'login' || viewState === 'register'">
        <form @submit.prevent="handleAuth" class="space-y-5">
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
            :disabled="isLoading || isGuestLoading"
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

        <!-- TEST AS GUEST BUTTON (Only on Login view) -->
        <div v-if="viewState === 'login'">
          <div class="mt-6 flex items-center justify-between">
            <span class="border-b border-darkpurple/10 w-1/5 lg:w-1/4"></span>
            <p class="text-xs text-center text-darkpurple-light font-bold uppercase">Or</p>
            <span class="border-b border-darkpurple/10 w-1/5 lg:w-1/4"></span>
          </div>

          <button
            @click.prevent="handleGuestLogin"
            :disabled="isGuestLoading || isLoading"
            class="w-full mt-6 bg-brokenwhite hover:bg-darkpurple/5 text-darkpurple-dark border border-darkpurple/10 font-bold py-3 px-6 rounded-xl transition-all flex justify-center items-center gap-2 disabled:opacity-50">
            <svg v-if="isGuestLoading" class="animate-spin h-5 w-5 text-darkpurple-dark" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isGuestLoading ? "Creating Isolated Session..." : "Test as Guest" }}
          </button>
        </div>
      </div>

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
  const isGuestLoading = ref(false);
  const errorMessage = ref("");

  const fullName = ref("");
  const email = ref("");
  const password = ref("");
  const confirmPassword = ref("");
  const code = ref("");

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

        const cognitoUser = await registerUser(email.value, password.value, fullName.value);
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

  async function handleGuestLogin() {
    isGuestLoading.value = true;
    errorMessage.value = "";

    try {
      // 1. Generate unique session ID for DynamoDB partition
      authStore.setGuestSession(crypto.randomUUID());

      // 2. Authenticate the demo user silently
      const token = await loginUser("demo@haikalahnaf.my.id", "PortfolioDemo123!");

      // 3. Set the token and redirect to dashboard
      authStore.setToken(token);
      router.push("/");
    } catch (error) {
      console.error(error);
      errorMessage.value = "Failed to initiate guest session. Please try again.";
    } finally {
      isGuestLoading.value = false;
    }
  }

  async function handleVerify() {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      await verifyEmail(actualUsername.value, code.value);
      const token = await loginUser(email.value, password.value);
      authStore.setToken(token);
      router.push("/");
    } catch (error) {
      errorMessage.value = error.message || error;
    } finally {
      isLoading.value = false;
    }
  }
</script>
