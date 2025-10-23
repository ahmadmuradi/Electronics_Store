import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { v4 as uuidv4 } from 'uuid';

import apiClient from './apiClient';

// Constants
const CACHE_KEY_PREFIX = '@ProductsCache';
const CACHE_DURATION = 15 * 60 * 1000; // 15 minutes
const OFFLINE_QUEUE_KEY = '@OfflineProductUpdates';

// Cache helper functions
const getCacheKey = key => `${CACHE_KEY_PREFIX}:${key}`;

const getCachedData = async key => {
  try {
    const cached = await AsyncStorage.getItem(getCacheKey(key));
    if (!cached) return null;

    const { data, timestamp, version = 1 } = JSON.parse(cached);
    const isExpired = Date.now() - timestamp > CACHE_DURATION;

    return { data, isExpired, version };
  } catch (error) {
    console.error('Error getting cached data:', error);
    return null;
  }
};

const setCachedData = async (key, data, version = 1) => {
  try {
    const cacheData = {
      data,
      timestamp: Date.now(),
      version,
    };
    await AsyncStorage.setItem(getCacheKey(key), JSON.stringify(cacheData));
    return true;
  } catch (error) {
    console.error('Error setting cache data:', error);
    return false;
  }
};

// Offline queue management
const addToOfflineQueue = async operation => {
  try {
    const queue = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
    const operations = queue ? JSON.parse(queue) : [];
    operations.push({
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      ...operation,
    });
    await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(operations));
    return operations.length;
  } catch (error) {
    console.error('Error adding to offline queue:', error);
    throw error;
  }
};

const processOfflineQueue = async token => {
  try {
    const queue = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
    if (!queue) return [];

    const operations = JSON.parse(queue);
    const successfulOps = [];
    const failedOps = [];

    for (const op of operations) {
      try {
        switch (op.type) {
          case 'UPDATE_STOCK':
            await updateProductStock(op.payload.productId, op.payload.quantity, token);
            successfulOps.push(op.id);
            break;
          // Add other operation types as needed
        }
      } catch (error) {
        console.error(`Error processing operation ${op.id}:`, error);
        failedOps.push({ ...op, error: error.message });
      }
    }

    // Update queue with failed operations
    await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(failedOps));

    return { successful: successfulOps.length, failed: failedOps.length };
  } catch (error) {
    console.error('Error processing offline queue:', error);
    throw error;
  }
};

// Product API functions with enhanced offline support
export const fetchProducts = async (token, forceRefresh = false) => {
  try {
    // Try to get from cache first if not forcing refresh
    if (!forceRefresh) {
      const cached = await getCachedData('all');
      if (cached && !cached.isExpired) {
        return { data: cached.data, fromCache: true };
      }
    }

    // Check network status
    const { isConnected } = await NetInfo.fetch();
    if (!isConnected) {
      const cached = await getCachedData('all');
      if (cached) {
        return { data: cached.data, fromCache: true, offline: true };
      }
      throw new Error('No internet connection and no cached data available');
    }

    // Fetch from API
    const products = await apiClient.get('/products', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Cache-Control': 'no-cache',
      },
    });

    // Update cache
    await setCachedData('all', products);

    return { data: products, fromCache: false };
  } catch (error) {
    console.error('Error fetching products:', error);
    // Return cached data if available, even if expired
    const cached = await getCachedData('all');
    if (cached) {
      return { data: cached.data, fromCache: true, error: error.message };
    }
    throw error;
  }
};

export const updateProductStock = async (productId, quantity, token) => {
  try {
    const { isConnected } = await NetInfo.fetch();

    // Prepare the update data
    const updateData = { quantity };

    if (isConnected) {
      // If online, update the server
      const updatedProduct = await apiClient.put(`/products/${productId}/stock`, updateData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      // Update local cache
      const cached = await getCachedData('all');
      if (cached) {
        const updatedProducts = cached.data.map(product =>
          product.id === productId
            ? { ...product, stock_quantity: quantity, updatedAt: new Date().toISOString() }
            : product
        );
        await setCachedData('all', updatedProducts, (cached.version || 1) + 1);
      }

      return { success: true, data: updatedProduct, fromServer: true };
    } else {
      // If offline, add to queue
      await addToOfflineQueue({
        type: 'UPDATE_STOCK',
        payload: { productId, quantity },
      });

      // Update local cache optimistically
      const cached = await getCachedData('all');
      if (cached) {
        const updatedProducts = cached.data.map(product =>
          product.id === productId
            ? {
                ...product,
                stock_quantity: quantity,
                pendingSync: true,
                updatedAt: new Date().toISOString(),
              }
            : product
        );
        await setCachedData('all', updatedProducts, (cached.version || 1) + 1);
      }

      return {
        success: true,
        data: { id: productId, stock_quantity: quantity, pendingSync: true },
        fromServer: false,
        queued: true,
      };
    }
  } catch (error) {
    console.error('Error updating product stock:', error);
    throw error;
  }
};

export const getProductDetails = async (productId, token) => {
  try {
    // Try to get from cache first
    const cached = await getCachedData(`product_${productId}`);
    if (cached && !cached.isExpired) {
      return { data: cached.data, fromCache: true };
    }

    const { isConnected } = await NetInfo.fetch();
    if (!isConnected) {
      if (cached) {
        return { data: cached.data, fromCache: true, offline: true };
      }
      throw new Error('No internet connection and no cached data available');
    }

    const product = await apiClient.get(`/products/${productId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Cache-Control': 'no-cache',
      },
    });

    // Update cache
    await setCachedData(`product_${productId}`, product);

    return { data: product, fromCache: false };
  } catch (error) {
    console.error(`Error fetching product ${productId}:`, error);
    const cached = await getCachedData(`product_${productId}`);
    if (cached) {
      return { data: cached.data, fromCache: true, error: error.message };
    }
    throw error;
  }
};

// Clear all cached product data
export const clearProductCache = async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter(key => key.startsWith(CACHE_KEY_PREFIX));
    await AsyncStorage.multiRemove(cacheKeys);
    return true;
  } catch (error) {
    console.error('Error clearing product cache:', error);
    return false;
  }
};

// Process pending offline operations
export const syncPendingOperations = async token => {
  try {
    const result = await processOfflineQueue(token);
    return result;
  } catch (error) {
    console.error('Error syncing pending operations:', error);
    throw error;
  }
};

// Get pending sync count
export const getPendingSyncCount = async () => {
  try {
    const queue = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
    return queue ? JSON.parse(queue).length : 0;
  } catch (error) {
    console.error('Error getting pending sync count:', error);
    return 0;
  }
};
