// Shared types for the application

export interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  quantity: number;
  sku: string;
  category: string;
  imageUrl?: string;
  lastUpdated: string;
  createdAt: string;
  barcode?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'staff' | 'viewer';
  firstName?: string;
  lastName?: string;
}

export interface SyncQueueItem {
  id: string;
  type: string;
  payload: any;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  attempts: number;
  createdAt: string;
  updatedAt?: string;
  error?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  timestamp?: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  status: 'success' | 'error' | 'loading';
  timestamp: string;
}

// Navigation types
declare global {
  namespace ReactNavigation {
    interface RootParamList {
      ProductList: undefined;
      ProductDetail: { productId: string };
      StockUpdate: { productId: string };
    }
  }
}
