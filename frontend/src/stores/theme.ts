import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // State: true for dark mode, false for light mode
  const isDark = ref(false);

  // Initialize from localStorage if available
  if (localStorage.getItem('theme') === 'dark') {
    isDark.value = true;
    document.documentElement.classList.add('dark');
  } else {
    localStorage.setItem('theme', 'light');
  }

  // Computed: get current theme
  const currentTheme = computed(() => isDark.value ? 'dark' : 'light');

  // Action: toggle theme
  function toggleTheme() {
    isDark.value = !isDark.value;
    if (isDark.value) {
      localStorage.setItem('theme', 'dark');
      document.documentElement.classList.add('dark');
    } else {
      localStorage.setItem('theme', 'light');
      document.documentElement.classList.remove('dark');
    }
  }

  // Action: set theme explicitly
  function setTheme(theme: 'light' | 'dark') {
    isDark.value = theme === 'dark';
    localStorage.setItem('theme', theme);
    if (isDark.value) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  return {
    isDark,
    currentTheme,
    toggleTheme,
    setTheme
  };
});