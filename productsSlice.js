import NetInfo from '@react-native-community/netinfo';
import { createSlice, createAsyncThunk, createSelector } from '@reduxjs/toolkit';

import {
  fetchProducts,
  updateProductStock,
  getPendingSyncCount,
  syncPendingOperations,
  getProductDetails as getProductDetailsService,
} from '../../services/products';

import { addToSyncQueue, processSyncQueue } from './syncQueueSlice';

// Async thunks
export const fetchProductsList = createAsyncThunk(
  'products/fetchAll',
  async (forceRefresh = false, { rejectWithValue, getState, dispatch }) => {
    try {
      const { auth } = getState();
      const {
        data: products,
        fromCache,
        offline,
        error,
      } = await fetchProducts(auth.token, forceRefresh);

      // If we're online and have pending sync operations, process them
      const { isConnected } = await NetInfo.fetch();
      if (isConnected) {
        const pendingCount = await getPendingSyncCount();
        if (pendingCount > 0) {
          dispatch(processSyncQueue());
        }
      }

      return { products, fromCache, offline, error };
    } catch (error) {
      return rejectWithValue({
        message: error.message,
        code: error.code,
        fromCache: error.fromCache || false,
        offline: !(await NetInfo.fetch()).isConnected,
      });
    }
  }
);

export const updateProductQuantity = createAsyncThunk(
  'products/updateQuantity',
  async ({ productId, quantity }, { dispatch, rejectWithValue, getState }) => {
    try {
      const { auth, products } = getState();
      const product = products.items.find(p => p.id === productId);

      if (!product) {
        throw new Error('Product not found');
      }

      // Optimistic update
      dispatch(updateProductStockLocal({ productId, quantity }));

      // Get network status
      const { isConnected } = await NetInfo.fetch();

      if (isConnected) {
        // If online, update the server
        const { data: updatedProduct } = await updateProductStock(productId, quantity, auth.token);

        return { product: updatedProduct, fromServer: true };
      } else {
        // If offline, add to sync queue
        const operation = {
          type: 'UPDATE_PRODUCT_STOCK',
          payload: { productId, quantity },
          meta: {
            timestamp: new Date().toISOString(),
            optimisticData: { ...product, quantity },
          },
        };

        dispatch(addToSyncQueue(operation));
        return {
          product: { ...product, quantity, pendingSync: true },
          fromServer: false,
        };
      }
    } catch (error) {
      // Revert optimistic update on error
      dispatch(revertProductUpdate({ productId }));
      return rejectWithValue({
        message: error.message,
        code: error.code,
        productId,
      });
    }
  }
);

export const getProductDetails = createAsyncThunk(
  'products/getDetails',
  async (productId, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const {
        data: product,
        fromCache,
        offline,
      } = await getProductDetailsService(productId, auth.token);

      return { product, fromCache, offline };
    } catch (error) {
      return rejectWithValue({
        message: error.message,
        code: error.code,
        productId,
        fromCache: error.fromCache || false,
        offline: !(await NetInfo.fetch()).isConnected,
      });
    }
  }
);

const initialState = {
  items: [],
  status: 'idle',
  error: null,
  lastUpdated: null,
  lastSync: null,
  pendingSyncCount: 0,
  isOnline: true,
};

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    clearProductsError: state => {
      state.error = null;
    },
    updateProductStockLocal: (state, action) => {
      const { productId, quantity } = action.payload;
      const product = state.items.find(p => p.id === productId);
      if (product) {
        product.quantity = quantity;
        product.updatedAt = new Date().toISOString();
        product.pendingSync = true;
      }
    },
    revertProductUpdate: (state, action) => {
      const { productId } = action.payload;
      const productIndex = state.items.findIndex(p => p.id === productId);
      if (productIndex !== -1 && state.items[productIndex].originalState) {
        state.items[productIndex] = state.items[productIndex].originalState;
      }
    },
    setOnlineStatus: (state, action) => {
      state.isOnline = action.payload;
      if (action.payload) {
        state.lastSync = new Date().toISOString();
      }
    },
    updatePendingSyncCount: (state, action) => {
      state.pendingSyncCount = action.payload;
    },
  },
  extraReducers: builder => {
    builder
      // Fetch Products List
      .addCase(fetchProductsList.pending, state => {
        state.status = 'loading';
      })
      .addCase(fetchProductsList.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload.products;
        state.lastUpdated = new Date().toISOString();
        if (action.payload.fromCache) {
          state.lastSync = 'Using cached data';
        } else {
          state.lastSync = new Date().toISOString();
        }
        state.error = null;
      })
      .addCase(fetchProductsList.rejected, (state, action) => {
        state.status = 'failed';
        state.error = {
          message: action.payload?.message || 'Failed to fetch products',
          code: action.payload?.code,
          fromCache: action.payload?.fromCache || false,
          offline: action.payload?.offline || false,
        };
      })

      // Update Product Quantity
      .addCase(updateProductQuantity.fulfilled, (state, action) => {
        const { product, fromServer } = action.payload;
        const index = state.items.findIndex(p => p.id === product.id);

        if (index !== -1) {
          state.items[index] = {
            ...state.items[index],
            ...product,
            pendingSync: !fromServer,
            updatedAt: new Date().toISOString(),
          };

          if (fromServer) {
            state.pendingSyncCount = Math.max(0, state.pendingSyncCount - 1);
          }
        }
      })
      .addCase(updateProductQuantity.rejected, (state, action) => {
        state.error = {
          message: action.payload?.message || 'Failed to update product quantity',
          code: action.payload?.code,
          productId: action.payload?.productId,
        };
      })

      // Get Product Details
      .addCase(getProductDetails.fulfilled, (state, action) => {
        const { product, fromCache } = action.payload;
        const index = state.items.findIndex(p => p.id === product.id);

        if (index === -1) {
          state.items.push(product);
        } else {
          state.items[index] = { ...state.items[index], ...product };
        }

        if (fromCache) {
          state.lastSync = 'Using cached data';
        } else {
          state.lastSync = new Date().toISOString();
        }
      });
  },
});

export const {
  clearProductsError,
  updateProductStockLocal,
  revertProductUpdate,
  setOnlineStatus,
  updatePendingSyncCount,
} = productsSlice.actions;

export default productsSlice.reducer;

// Selectors
const selectProductsState = state => state.products;

export const selectAllProducts = createSelector(
  [selectProductsState],
  productsState => productsState.items
);

export const selectProductById = productId =>
  createSelector([selectAllProducts], products => products.find(p => p.id === productId));

export const selectProductsStatus = createSelector([selectProductsState], productsState => ({
  status: productsState.status,
  error: productsState.error,
  lastUpdated: productsState.lastUpdated,
  lastSync: productsState.lastSync,
  isOnline: productsState.isOnline,
  pendingSyncCount: productsState.pendingSyncCount,
}));

// Add network status listener
export const setupNetworkListeners = () => dispatch => {
  // Initial network state
  NetInfo.fetch().then(state => {
    dispatch(setOnlineStatus(state.isConnected));
  });

  // Subscribe to network state changes
  return NetInfo.addEventListener(state => {
    const wasOffline = !state.isConnected;
    dispatch(setOnlineStatus(state.isConnected));

    // If we just came back online, trigger a sync
    if (wasOffline && state.isConnected) {
      dispatch(processSyncQueue());
      dispatch(fetchProductsList(true)); // Force refresh
    }
  });
};
