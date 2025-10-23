import * as BackgroundFetch from 'expo-background-fetch';
import * as Notifications from 'expo-notifications';
import * as TaskManager from 'expo-task-manager';
import { Platform } from 'react-native';

import apiClient from './apiClient';

// Background sync task name
const SYNC_TASK_NAME = 'background-sync-task';

// Process a single sync item
const processSyncItem = async (item, token) => {
  try {
    switch (item.type) {
      case 'UPDATE_PRODUCT_STOCK':
        const { productId, quantity } = item.payload;
        await apiClient.put(
          `/products/${productId}/stock`,
          { quantity },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        break;

      // Add more sync item types as needed

      default:
        console.warn(`Unknown sync item type: ${item.type}`);
        return { success: false, error: 'Unknown sync item type' };
    }

    return { success: true };
  } catch (error) {
    console.error(`Error processing sync item ${item.id}:`, error);
    return {
      success: false,
      error: error.message || 'Failed to process sync item',
      retryable: isRetryableError(error),
    };
  }
};

// Check if an error is retryable
const isRetryableError = error => {
  if (!error.status) return true; // Default to retryable if we can't determine the status

  // Don't retry 4xx errors except for 408 (Request Timeout) and 429 (Too Many Requests)
  if (error.status >= 400 && error.status < 500 && error.status !== 408 && error.status !== 429) {
    return false;
  }

  return true;
};

// Process the entire sync queue
export const processSyncQueue = async (items, token) => {
  if (!items || items.length === 0) return [];

  const results = [];

  for (const item of items) {
    // Skip items that have exceeded max retries
    if (item.attempts >= 3) {
      results.push({
        id: item.id,
        success: false,
        error: 'Max retries exceeded',
        retryable: false,
      });
      continue;
    }

    const result = await processSyncItem(item, token);
    results.push({
      id: item.id,
      success: result.success,
      error: result.error,
      retryable: result.retryable !== false, // Default to true if not specified
    });

    // Add a small delay between processing items to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  return results;
};

// Register the background task
const registerBackgroundSyncTask = async () => {
  try {
    // Check if task is already registered
    const isRegistered = await TaskManager.isTaskRegisteredAsync(SYNC_TASK_NAME);

    if (!isRegistered) {
      // Define the background task
      TaskManager.defineTask(SYNC_TASK_NAME, async () => {
        try {
          const { token } = await getAuthState();
          if (!token) {
            console.log('No auth token available for background sync');
            return BackgroundFetch.Result.NoData;
          }

          // Get pending sync items from storage
          const pendingItems = await getPendingSyncItems();

          if (pendingItems.length === 0) {
            console.log('No pending items to sync');
            return BackgroundFetch.Result.NoData;
          }

          console.log(`Processing ${pendingItems.length} items in background sync`);

          // Process the queue
          const results = await processSyncQueue(pendingItems, token);

          // Update sync status based on results
          const failedItems = results.filter(r => !r.success);

          if (failedItems.length > 0) {
            console.warn(`${failedItems.length} items failed to sync`);
            // You might want to show a notification here
            if (Platform.OS === 'ios' || Platform.OS === 'android') {
              await Notifications.scheduleNotificationAsync({
                content: {
                  title: 'Sync Incomplete',
                  body: `${failedItems.length} items failed to sync. Please check your connection.`,
                },
                trigger: null,
              });
            }
          } else {
            console.log('Background sync completed successfully');
          }

          return BackgroundFetch.Result.NewData;
        } catch (error) {
          console.error('Background sync error:', error);
          return BackgroundFetch.Result.Failed;
        }
      });

      // Register the task to run periodically
      await BackgroundFetch.registerTaskAsync(SYNC_TASK_NAME, {
        minimumInterval: 15 * 60, // 15 minutes
        stopOnTerminate: false,
        startOnBoot: true,
      });

      console.log('Background sync task registered');
    }
  } catch (error) {
    console.error('Error registering background sync task:', error);
  }
};

// Unregister the background task
const unregisterBackgroundSyncTask = async () => {
  try {
    await BackgroundFetch.unregisterTaskAsync(SYNC_TASK_NAME);
    console.log('Background sync task unregistered');
  } catch (error) {
    console.error('Error unregistering background sync task:', error);
  }
};

// Get pending sync items from storage
const getPendingSyncItems = async () => {
  try {
    const pendingItems = await AsyncStorage.getItem('@SyncQueue:pending');
    return pendingItems ? JSON.parse(pendingItems) : [];
  } catch (error) {
    console.error('Error getting pending sync items:', error);
    return [];
  }
};

// Initialize sync service
export const initSyncService = async () => {
  // Request necessary permissions
  if (Platform.OS === 'ios' || Platform.OS === 'android') {
    await Notifications.requestPermissionsAsync({
      ios: {
        allowAlert: true,
        allowBadge: true,
        allowSound: true,
      },
    });
  }

  // Register background sync task
  await registerBackgroundSyncTask();

  return {
    registerBackgroundSyncTask,
    unregisterBackgroundSyncTask,
  };
};

export default {
  processSyncQueue,
  initSyncService,
  registerBackgroundSyncTask,
  unregisterBackgroundSyncTask,
};
