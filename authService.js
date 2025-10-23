import * as Sentry from 'sentry-expo';

import { config, STORAGE_KEYS, secureStorage } from '../config/config';

class AuthService {
  constructor() {
    this.isRefreshing = false;
    this.failedQueue = [];
  }

  async login(credentials) {
    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      await this.setAuthData(data);
      return data;
    } catch (error) {
      Sentry.Native.captureException(error, {
        tags: { type: 'auth', action: 'login' },
      });
      throw error;
    }
  }

  async refreshToken() {
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.failedQueue.push({ resolve, reject });
      });
    }

    this.isRefreshing = true;
    const refreshToken = await secureStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

    if (!refreshToken) {
      this.isRefreshing = false;
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      await this.setAuthData(data);
      this.processQueue(null, data.access_token);
      return data.access_token;
    } catch (error) {
      this.processQueue(error, null);
      await this.logout();
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  async setAuthData({ access_token, refresh_token, user, expires_in = 3600 }) {
    const expiryTime = new Date().getTime() + expires_in * 1000;

    await Promise.all([
      secureStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, access_token),
      refresh_token && secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh_token),
      secureStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user)),
      secureStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRY, expiryTime.toString()),
    ]);
  }

  async isTokenExpired() {
    const expiryTime = await secureStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRY);
    if (!expiryTime) return true;
    return new Date().getTime() > parseInt(expiryTime, 10);
  }

  async getAuthToken() {
    if (await this.isTokenExpired()) {
      return this.refreshToken();
    }
    return secureStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  async getCurrentUser() {
    const userData = await secureStorage.getItem(STORAGE_KEYS.USER_DATA);
    return userData ? JSON.parse(userData) : null;
  }

  async logout() {
    await Promise.all([
      secureStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN),
      secureStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
      secureStorage.removeItem(STORAGE_KEYS.USER_DATA),
      secureStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRY),
    ]);
  }

  processQueue(error, token = null) {
    this.failedQueue.forEach(promise => {
      if (error) {
        promise.reject(error);
      } else {
        promise.resolve(token);
      }
    });
    this.failedQueue = [];
  }
}

export const authService = new AuthService();
