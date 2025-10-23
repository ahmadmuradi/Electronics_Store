import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SyncQueueState {
  queue: Array<{
    type: string;
    payload: any;
    meta?: any;
  }>;
  isSyncing: boolean;
}

const initialState: SyncQueueState = {
  queue: [],
  isSyncing: false,
};

const syncQueueSlice = createSlice({
  name: 'syncQueue',
  initialState,
  reducers: {
    addToQueue: (state, action: PayloadAction<{ type: string; payload: any; meta?: any }>) => {
      state.queue.push(action.payload);
    },
    removeFromQueue: (state, action: PayloadAction<number>) => {
      state.queue.splice(action.payload, 1);
    },
    setSyncing: (state, action: PayloadAction<boolean>) => {
      state.isSyncing = action.payload;
    },
    clearQueue: state => {
      state.queue = [];
      state.isSyncing = false;
    },
  },
});

export const { addToQueue, removeFromQueue, setSyncing, clearQueue } = syncQueueSlice.actions;

export const selectIsSyncing = (state: { syncQueue: SyncQueueState }) => state.syncQueue.isSyncing;
export const selectQueue = (state: { syncQueue: SyncQueueState }) => state.syncQueue.queue;

export default syncQueueSlice.reducer;
