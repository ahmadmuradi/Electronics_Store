import NetInfo from '@react-native-community/netinfo';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { processQueue } from '../store/slices/syncQueue';
import { selectIsSyncing } from '../store/slices/syncQueue';

/**
 * Custom hook to monitor network connectivity and trigger sync when online
 * @param {boolean} [autoSync=true] - Whether to automatically trigger sync when online
 * @returns {Object} - Connectivity state and sync status
 */
const useConnectivity = (autoSync = true) => {
  const dispatch = useDispatch();
  const isSyncing = useSelector(selectIsSyncing);

  useEffect(() => {
    // Subscribe to network state updates
    const unsubscribe = NetInfo.addEventListener(state => {
      if (state.isConnected && state.isInternetReachable && autoSync) {
        // Trigger sync when coming back online
        dispatch(processQueue());
      }
    });

    // Initial check
    const checkConnectivity = async () => {
      const state = await NetInfo.fetch();
      if (state.isConnected && state.isInternetReachable && autoSync) {
        dispatch(processQueue());
      }
    };

    checkConnectivity();

    // Cleanup subscription on unmount
    return () => {
      unsubscribe();
    };
  }, [dispatch, autoSync]);

  // Return sync status and other connectivity info
  return {
    isSyncing,
  };
};

export default useConnectivity;
