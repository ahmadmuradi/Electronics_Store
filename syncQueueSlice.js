import { createSlice, createAsyncThunk, createSelector } from '@reduxjs/toolkit';

import { processSyncQueue } from '../../services/sync';

// Helper to generate unique ID for each sync item
const generateId = () => Math.random().toString(36).substr(2, 9);

// Async thunk to process the sync queue
export const processQueue = createAsyncThunk(
  'syncQueue/process',
  async (_, { getState, rejectWithValue, dispatch }) => {
    try {
      const { syncQueue, auth } = getState();
      const pendingItems = syncQueue.items.filter(item => item.status === 'pending');

      if (pendingItems.length === 0) return [];

      const results = await processSyncQueue(pendingItems, auth.token);

      // Mark processed items as completed or failed
      results.forEach(result => {
        if (result.success) {
          dispatch(markAsCompleted(result.id));
        } else {
          dispatch(markAsFailed({ id: result.id, error: result.error }));
        }
      });

      return results;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const initialState = {
  items: [],
  status: 'idle', // 'idle' | 'processing' | 'succeeded' | 'failed'
  error: null,
  lastSync: null,
};

const syncQueueSlice = createSlice({
  name: 'syncQueue',
  initialState,
  reducers: {
    addToQueue: (state, action) => {
      state.items.push({
        id: generateId(),
        ...action.payload,
        status: 'pending',
        createdAt: new Date().toISOString(),
        attempts: 0,
      });
    },
    markAsProcessing: (state, action) => {
      const item = state.items.find(item => item.id === action.payload);
      if (item) {
        item.status = 'processing';
        item.attempts += 1;
        item.lastAttempt = new Date().toISOString();
      }
    },
    markAsCompleted: (state, action) => {
      const item = state.items.find(item => item.id === action.payload);
      if (item) {
        item.status = 'completed';
        item.completedAt = new Date().toISOString();
      }
      state.lastSync = new Date().toISOString();
    },
    markAsFailed: (state, action) => {
      const { id, error } = action.payload;
      const item = state.items.find(item => item.id === id);
      if (item) {
        item.status = 'failed';
        item.error = error;
        item.lastError = new Date().toISOString();
      }
    },
    removeFromQueue: (state, action) => {
      state.items = state.items.filter(item => item.id !== action.payload);
    },
    clearCompleted: state => {
      state.items = state.items.filter(item => item.status !== 'completed');
    },
  },
  extraReducers: builder => {
    builder
      .addCase(processQueue.pending, state => {
        state.status = 'processing';
      })
      .addCase(processQueue.fulfilled, state => {
        state.status = 'succeeded';
        state.lastSync = new Date().toISOString();
      })
      .addCase(processQueue.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export const {
  addToQueue,
  markAsProcessing,
  markAsCompleted,
  markAsFailed,
  removeFromQueue,
  clearCompleted,
} = syncQueueSlice.actions;

export default syncQueueSlice.reducer;

// Selectors
export const selectSyncQueue = state => state.syncQueue;

export const selectPendingSyncItems = createSelector([selectSyncQueue], syncQueue =>
  syncQueue.items.filter(item => item.status === 'pending')
);

export const selectFailedSyncItems = createSelector([selectSyncQueue], syncQueue =>
  syncQueue.items.filter(item => item.status === 'failed')
);

export const selectIsSyncing = state => state.syncQueue.status === 'processing';
