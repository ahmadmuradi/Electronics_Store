import NetInfo from '@react-native-community/netinfo';
import Constants from 'expo-constants';
import * as Sentry from 'sentry-expo';

import { config } from '../config/config';

import { authService } from './authService';

// Constants
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second
const UNAUTHORIZED = 401;
const FORBIDDEN = 403;

// Request queue for token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Track request metrics
const trackRequest = (url, method, status, duration, error = null) => {
  const metric = {
    url,
    method,
    status,
    duration,
    timestamp: new Date().toISOString(),
  };

  if (error) {
    Sentry.Native.addBreadcrumb({
      category: 'api.error',
      message: `API Error: ${method} ${url}`,
      data: { error: error.message, status: error.status },
      level: 'error',
    });
  }

  // Here you can add code to send metrics to your analytics service
  console.debug('API Request:', metric);
};

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

const fetchWithRetry = async (url, options = {}, retries = 0, isRetry = false) => {
  const startTime = Date.now();
  let response;

  try {
    // Check network connectivity
    const isConnected = (await NetInfo.fetch()).isConnected;
    if (!isConnected) {
      throw new Error('No internet connection');
    }

    // Get auth token for the request
    const token = await authService.getAuthToken();

    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    // Make the request
    const requestUrl = `${config.API_BASE_URL}${url}`;
    response = await fetch(requestUrl, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized with token refresh
    if (response.status === UNAUTHORIZED && !isRetry) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          await authService.refreshToken();
          isRefreshing = false;
          processQueue(null, true);
          // Retry the original request with new token
          return fetchWithRetry(url, options, retries, true);
        } catch (error) {
          processQueue(error, null);
          throw error;
        } finally {
          isRefreshing = false;
        }
      } else {
        // If token is already being refreshed, queue the request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => fetchWithRetry(url, options, retries, true))
          .catch(error => {
            throw error;
          });
      }
    }

    // Log response metrics
    const duration = Date.now() - startTime;
    trackRequest(url, options.method || 'GET', response.status, duration);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.message || `HTTP error! status: ${response.status}`);
      error.status = response.status;
      error.data = errorData;

      // Log 4xx and 5xx errors to Sentry
      if (response.status >= 400) {
        Sentry.Native.captureException(error, {
          tags: {
            type: 'api',
            status: response.status,
            method: options.method || 'GET',
            url,
          },
          extra: { errorData },
        });
      }

      throw error;
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    return await response.text();
  } catch (error) {
    const duration = Date.now() - startTime;
    trackRequest(url, options.method || 'GET', error.status || 0, duration, error);

    if (retries < MAX_RETRIES && !isAuthError(error)) {
      const delayMs = RETRY_DELAY * Math.pow(2, retries);
      console.log(`Retrying (${retries + 1}/${MAX_RETRIES}) in ${delayMs}ms...`);
      await delay(delayMs);
      return fetchWithRetry(url, options, retries + 1, isRetry);
    }

    throw error;
  }
};

// Helper to check if error is an authentication error
const isAuthError = error => {
  return error.status === UNAUTHORIZED || error.status === FORBIDDEN;
};

// delay function is already defined above

// Set the auth token for subsequent requests (deprecated - use authService instead)
const setAuthToken = token => {
  console.warn('setAuthToken is deprecated. Use authService instead.');
};

// Clear the auth token (deprecated - use authService instead)
const clearAuthToken = () => {
  console.warn('clearAuthToken is deprecated. Use authService.logout() instead.');
};

// HTTP methods with enhanced error handling and logging
const apiClient = {
  get: async (url, options = {}) => {
    try {
      return await fetchWithRetry(url, {
        ...options,
        method: 'GET',
      });
    } catch (error) {
      throw enhanceError(error, 'GET', url);
    }
  },

  post: async (url, data, options = {}) => {
    try {
      return await fetchWithRetry(url, {
        ...options,
        method: 'POST',
        body: JSON.stringify(data),
      });
    } catch (error) {
      throw enhanceError(error, 'POST', url, data);
    }
  },

  put: async (url, data, options = {}) => {
    try {
      return await fetchWithRetry(url, {
        ...options,
        method: 'PUT',
        body: JSON.stringify(data),
      });
    } catch (error) {
      throw enhanceError(error, 'PUT', url, data);
    }
  },

  delete: async (url, options = {}) => {
    try {
      return await fetchWithRetry(url, {
        ...options,
        method: 'DELETE',
      });
    } catch (error) {
      throw enhanceError(error, 'DELETE', url);
    }
  },

  // Add a method to track sync operations
  trackSync: async (operation, status, metadata = {}) => {
    try {
      await apiClient.post('/sync/logs', {
        operation,
        status,
        metadata: {
          ...metadata,
          timestamp: new Date().toISOString(),
          deviceId: Constants.deviceId,
          version: Constants.expoConfig?.version || 'unknown',
        },
      });
    } catch (error) {
      // Don't throw for sync tracking failures
      console.warn('Failed to track sync operation:', error);
    }
  },

  // Deprecated methods (kept for backward compatibility)
  setAuthToken,
  clearAuthToken,
};

// Helper to enhance error with additional context
const enhanceError = (error, method, url, data = null) => {
  error.config = { method, url, data };
  return error;
};

export default apiClient;
