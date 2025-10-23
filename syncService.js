import AsyncStorage from '@react-native-async-storage/async-storage';
import { NetInfo } from '@react-native-community/netinfo';
import * as Sentry from 'sentry-expo';

import apiClient from './apiClient';
import { authService } from './authService';

const SYNC_QUEUE_KEY = '@sync_queue';
const MAX_RETRIES = 3;
const SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes

class SyncService {
  constructor() {
    this.isSyncing = false;
    this.syncListeners = new Set();
    this.syncInterval = null;
  }

  async init() {
    // Start periodic sync
    this.syncInterval = setInterval(() => this.syncIfOnline(), SYNC_INTERVAL);

    // Sync when app comes back online
    NetInfo.addEventListener(state => {
      if (state.isConnected) {
        this.syncIfOnline();
      }
    });
  }

  async addToQueue(operation) {
    if (!operation.id) {
      operation.id = Date.now().toString();
    }

    try {
      const queue = await this.getQueue();
      queue.push({
        ...operation,
        createdAt: new Date().toISOString(),
        status: 'pending',
        retryCount: 0,
      });

      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
      this.syncIfOnline();

      return operation.id;
    } catch (error) {
      console.error('Failed to add to sync queue:', error);
      Sentry.Native.captureException(error, {
        tags: { type: 'sync', action: 'add_to_queue' },
        extra: { operation },
      });
      throw error;
    }
  }

  async getQueue() {
    try {
      const queueJson = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      return queueJson ? JSON.parse(queueJson) : [];
    } catch (error) {
      console.error('Failed to get sync queue:', error);
      return [];
    }
  }

  async clearQueue() {
    try {
      await AsyncStorage.removeItem(SYNC_QUEUE_KEY);
    } catch (error) {
      console.error('Failed to clear sync queue:', error);
      Sentry.Native.captureException(error, {
        tags: { type: 'sync', action: 'clear_queue' },
      });
    }
  }

  async syncIfOnline() {
    const { isConnected } = await NetInfo.fetch();
    if (isConnected && !this.isSyncing) {
      this.processQueue();
    }
  }

  async processQueue() {
    if (this.isSyncing) return;

    this.isSyncing = true;
    const queue = await this.getQueue();

    for (const item of queue) {
      if (item.status === 'completed') continue;

      try {
        // Skip if max retries reached
        if (item.retryCount >= MAX_RETRIES) {
          await this.updateItemStatus(item.id, 'failed', { error: 'Max retries reached' });
          continue;
        }

        // Process the operation
        await this.processItem(item);
      } catch (error) {
        console.error('Error processing sync item:', error);
        await this.handleSyncError(item, error);
      }
    }

    this.isSyncing = false;
  }

  async processItem(item) {
    const { type, payload } = item;

    // Update status to processing
    await this.updateItemStatus(item.id, 'processing');

    try {
      let result;

      switch (type) {
        case 'update_product':
          result = await apiClient.put(`/products/${payload.id}`, payload.data);
          break;

        case 'create_product':
          result = await apiClient.post('/products', payload);
          break;

        case 'delete_product':
          await apiClient.delete(`/products/${payload.id}`);
          break;

        default:
          throw new Error(`Unknown sync operation type: ${type}`);
      }

      // Mark as completed
      await this.updateItemStatus(item.id, 'completed', { result });

      // Log successful sync
      await apiClient.trackSync(type, 'success', {
        itemId: item.id,
        operationType: type,
        payload: payload,
      });
    } catch (error) {
      // Log failed sync
      await apiClient.trackSync(type, 'failed', {
        itemId: item.id,
        operationType: type,
        error: error.message,
        status: error.status,
        payload: payload,
      });

      throw error; // Re-throw to be handled by the caller
    }
  }

  async handleSyncError(item, error) {
    const queue = await this.getQueue();
    const itemIndex = queue.findIndex(i => i.id === item.id);

    if (itemIndex === -1) return;

    // Update retry count and status
    queue[itemIndex] = {
      ...queue[itemIndex],
      retryCount: (queue[itemIndex].retryCount || 0) + 1,
      status: 'pending',
      lastError: error.message,
      lastAttempt: new Date().toISOString(),
    };

    await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));

    // Log to Sentry
    Sentry.Native.captureException(error, {
      tags: {
        type: 'sync',
        action: 'process_item',
        operationType: item.type,
        retryCount: queue[itemIndex].retryCount,
      },
      extra: {
        item,
        error: error.message,
        stack: error.stack,
      },
    });
  }

  async updateItemStatus(id, status, data = {}) {
    const queue = await this.getQueue();
    const itemIndex = queue.findIndex(item => item.id === id);

    if (itemIndex === -1) return;

    queue[itemIndex] = {
      ...queue[itemIndex],
      status,
      updatedAt: new Date().toISOString(),
      ...data,
    };

    await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
    this.notifyListeners();
  }

  addSyncListener(listener) {
    this.syncListeners.add(listener);
    return () => this.syncListeners.delete(listener);
  }

  notifyListeners() {
    this.syncListeners.forEach(listener => {
      try {
        listener();
      } catch (error) {
        console.error('Error in sync listener:', error);
      }
    });
  }

  cleanup() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.syncListeners.clear();
  }
}

export const syncService = new SyncService();

// Initialize sync service when the app starts
syncService.init();

// Clean up on app close
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => syncService.cleanup());
}
