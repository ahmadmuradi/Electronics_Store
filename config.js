import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

// Default configuration
const defaultConfig = {
  API_BASE_URL: 'http://localhost:8001',
  ENV: 'development',
  SENTRY_DSN: null,
};

// Merge environment variables with defaults
const config = {
  ...defaultConfig,
  ...Constants.expoConfig?.extra,
};

// Secure storage keys
const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  TOKEN_EXPIRY: 'token_expiry',
};

// Secure storage methods
const secureStorage = {
  async getItem(key) {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      console.error('SecureStore getItem error:', error);
      return null;
    }
  },

  async setItem(key, value) {
    try {
      await SecureStore.setItemAsync(key, value);
      return true;
    } catch (error) {
      console.error('SecureStore setItem error:', error);
      return false;
    }
  },

  async removeItem(key) {
    try {
      await SecureStore.deleteItemAsync(key);
      return true;
    } catch (error) {
      console.error('SecureStore removeItem error:', error);
      return false;
    }
  },
};

export { config, STORAGE_KEYS, secureStorage };
