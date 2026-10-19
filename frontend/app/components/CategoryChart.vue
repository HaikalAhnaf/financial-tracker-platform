<template>
  <div class="bg-white p-6 rounded-xl shadow flex flex-col items-center h-full">
    <h3 class="text-lg font-bold text-gray-800 mb-4 self-start">{{ title }}</h3>
    <div class="relative w-full max-w-[220px] aspect-square flex-1 flex justify-center">
      <Doughnut v-if="hasData" :data="chartData" :options="chartOptions" />
      <p v-else class="text-gray-500 text-sm text-center absolute inset-0 flex items-center justify-center">No data for this month.</p>
    </div>
  </div>
</template>

<script setup>
  import { computed } from "vue";
  import { Doughnut } from "vue-chartjs";
  import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

  ChartJS.register(ArcElement, Tooltip, Legend);

  const props = defineProps({
    title: String,
    categoryData: Object,
    type: { type: String, default: "expense" },
  });

  const hasData = computed(() => Object.keys(props.categoryData).length > 0);

  const chartData = computed(() => {
    const isExpense = props.type === "expense";
    return {
      labels: Object.keys(props.categoryData),
      datasets: [
        {
          data: Object.values(props.categoryData),
          // Use warm colors for expenses, cool colors for income
          backgroundColor: isExpense
            ? ["#EF4444", "#F59E0B", "#F97316", "#EC4899", "#8B5CF6"]
            : ["#10B981", "#3B82F6", "#14B8A6", "#84CC16", "#06B6D4"],
          borderWidth: 0,
          hoverOffset: 4,
        },
      ],
    };
  });

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: "bottom" } },
  };
</script>
