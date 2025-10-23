import { configureStore } from '@reduxjs/toolkit';
import { combineReducers } from 'redux';

import authReducer from './slices/authSlice';
import productsReducer from './slices/productsSlice';
import syncQueueReducer from './slices/syncQueueSlice';

// Create a test reducer without persistence
const rootReducer = combineReducers({
  auth: authReducer,
  products: productsReducer,
  syncQueue: syncQueueReducer,
});

// Configure store with middleware
const store = configureStore({
  reducer: rootReducer,
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export { store };
