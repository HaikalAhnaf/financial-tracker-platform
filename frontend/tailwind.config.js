/** @type {import('tailwindcss').Config} */
export default {
  content: ["./app/**/*.{vue,js,ts}"],
  theme: {
    extend: {
      colors: {
        brokenwhite: "#F9F8F6", // Elegant off-white
        darkpurple: {
          DEFAULT: "#2D1B4E", // Primary brand purple
          light: "#4A327A", // Hover states
          dark: "#1A0B2E", // Deep text
        },
      },
    },
  },
};
