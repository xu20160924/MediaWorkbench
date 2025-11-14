import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('token') || null);
  const user = ref<any>(null);
  const isAuthenticated = computed(() => !!token.value);

  // Actions
  function setToken(newToken: string | null) {
    token.value = newToken;
    if (newToken) {
      localStorage.setItem('token', newToken);
    } else {
      localStorage.removeItem('token');
    }
  }

  function setUser(userData: any) {
    user.value = userData;
  }

  function logout() {
    setToken(null);
    user.value = null;
  }

  // Initialize from localStorage if available
  function initialize() {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      token.value = storedToken;
      // You might want to fetch user data here if needed
    }
  }

  // Initialize on store creation
  initialize();

  return {
    // State
    token,
    user,
    isAuthenticated,
    
    // Actions
    setToken,
    setUser,
    logout,
    initialize
  };
});
