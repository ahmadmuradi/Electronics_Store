import * as SecureStore from 'expo-secure-store';

import apiClient from './apiClient';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'user_data';

// Login user
export const login = async (username, password) => {
  try {
    const response = await apiClient.post('/auth/login', { username, password });

    // Store the token and user data
    await Promise.all([
      SecureStore.setItemAsync(TOKEN_KEY, response.token),
      SecureStore.setItemAsync(USER_KEY, JSON.stringify(response.user)),
    ]);

    // Set the auth token for subsequent requests
    apiClient.setAuthToken(response.token);

    return {
      user: response.user,
      token: response.token,
    };
  } catch (error) {
    console.error('Login error:', error);
    throw new Error(error.message || 'Failed to login');
  }
};

// Logout user
export const logout = async () => {
  try {
    await Promise.all([
      SecureStore.deleteItemAsync(TOKEN_KEY),
      SecureStore.deleteItemAsync(USER_KEY),
    ]);

    // Clear the auth token
    apiClient.clearAuthToken();

    return true;
  } catch (error) {
    console.error('Logout error:', error);
    throw new Error('Failed to logout');
  }
};

// Check if user is logged in
export const isLoggedIn = async () => {
  try {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    return !!token;
  } catch (error) {
    console.error('Error checking auth status:', error);
    return false;
  }
};

// Get the current user
export const getCurrentUser = async () => {
  try {
    const userData = await SecureStore.getItemAsync(USER_KEY);
    return userData ? JSON.parse(userData) : null;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
};

// Get the auth token
export const getAuthToken = async () => {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

// Initialize auth state
export const initializeAuth = async () => {
  try {
    const [token, userData] = await Promise.all([
      SecureStore.getItemAsync(TOKEN_KEY),
      SecureStore.getItemAsync(USER_KEY),
    ]);

    if (token) {
      apiClient.setAuthToken(token);
      return {
        isAuthenticated: true,
        user: userData ? JSON.parse(userData) : null,
        token,
      };
    }

    return { isAuthenticated: false, user: null, token: null };
  } catch (error) {
    console.error('Error initializing auth:', error);
    return { isAuthenticated: false, user: null, token: null };
  }
};
