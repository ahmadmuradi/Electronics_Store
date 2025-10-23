import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  FlatList,
  TextInput,
  Modal,
  Image,
  StatusBar,
  Platform,
  PermissionsAndroid,
  LogBox,
} from 'react-native';
import 'react-native-get-random-values';
import Icon from 'react-native-vector-icons/MaterialIcons';
import * as Sentry from 'sentry-expo';
import { v4 as uuidv4 } from 'uuid';
import * as SecureStore from 'expo-secure-store';
import NetInfo from '@react-native-community/netinfo';
// Camera functionality temporarily disabled for build
// import { Camera } from 'expo-camera';
// import { BarCodeScanner } from 'expo-barcode-scanner';

// Import services
import { sentry, ErrorBoundary } from './src/config/sentry';
import apiClient from './src/services/apiClient';
import { authService } from './src/services/authService';
import { syncService } from './src/services/syncService';

// Initialize Sentry
if (!__DEV__) {
  sentry; // Initialize Sentry in production
}

// Ignore specific warnings
LogBox.ignoreLogs(['Setting a timer', 'AsyncStorage has been extracted']);

export default function App() {
  const [isOnline, setIsOnline] = useState(true);
  const [products, setProducts] = useState([]);
  const [pendingSync, setPendingSync] = useState([]);
  const [showScanner, setShowScanner] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [stockAdjustment, setStockAdjustment] = useState('');
  const [authToken, setAuthToken] = useState(null);
  const [user, setUser] = useState(null);
  const [showLogin, setShowLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    // Set up auth state listener
    const setupAuth = async () => {
      try {
        const user = await authService.getCurrentUser();
        if (user) {
          setUser(user);
          setShowLogin(false);
          loadProducts();

          // Set Sentry user context
          if (sentry?.setUserContext) {
            sentry.setUserContext(user);
          }
        }
      } catch (error) {
        console.error('Auth setup error:', error);
        Sentry.Native.captureException(error, {
          tags: { type: 'auth', action: 'setup' },
        });
      }
    };

    // Monitor network connectivity
    const unsubscribeNetInfo = NetInfo.addEventListener(state => {
      const wasOffline = !isOnline && state.isConnected;
      setIsOnline(state.isConnected);

      // If we just came back online, trigger a sync
      if (wasOffline) {
        syncService.syncIfOnline();
      }
    });

    // Load initial data
    setupAuth();
    loadCachedData();

    // Set up sync listener
    const updateSyncStatus = () => {
      // Update UI based on sync status if needed
    };

    const unsubscribeSync = syncService.addSyncListener(updateSyncStatus);

    return () => {
      unsubscribeNetInfo();
      if (unsubscribeSync) unsubscribeSync();
    };
  }, []);

  // Authentication
  const login = async () => {
    try {
      setLoading(true);

      // Track login attempt
      Sentry.Native.addBreadcrumb({
        category: 'auth',
        message: 'User login attempt',
        level: 'info',
        data: { username },
      });

      const data = await authService.login({ username, password });

      setUser(data.user);
      setShowLogin(false);

      // Set Sentry user context
      if (sentry?.setUserContext) {
        sentry.setUserContext(data.user);
      }

      // Load products after successful login
      await loadProducts();

      // Track successful login
      Sentry.Native.addBreadcrumb({
        category: 'auth',
        message: 'User logged in successfully',
        level: 'info',
        data: { userId: data.user.id },
      });
    } catch (error) {
      console.error('Login error:', error);

      // Track failed login attempt
      Sentry.Native.captureException(error, {
        tags: { type: 'auth', action: 'login_failed' },
        extra: { username },
      });

      Alert.alert(
        'Login Failed',
        error.message || 'An error occurred during login. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Load cached data from storage
  const loadCachedData = async () => {
    try {
      // Try to load user from secure storage
      const user = await authService.getCurrentUser();
      if (user) {
        setUser(user);
        setShowLogin(false);
      }

      // Load cached products
      const cachedProducts = await AsyncStorage.getItem('products');
      if (cachedProducts) {
        setProducts(JSON.parse(cachedProducts));
      }

      // Log app start
      apiClient.trackSync('app_start', 'info', {
        isOnline,
        user: user ? user.id : 'anonymous',
        productCount: cachedProducts ? JSON.parse(cachedProducts).length : 0,
      });

      if (cachedPending) {
        setPendingSync(JSON.parse(cachedPending));
      }
    } catch (error) {
      console.error('Error loading cached data:', error);
    }
  };

  // Load products from API or cache
  const loadProducts = async () => {
    const startTime = Date.now();

    try {
      // Try to fetch fresh data if online
      if (isOnline) {
        const data = await apiClient.get('/products');

        // Merge with any pending changes
        const pendingOperations = await syncService.getQueue();
        const pendingUpdates = {};

        pendingOperations.forEach(op => {
          if (op.type === 'update_product') {
            pendingUpdates[op.payload.id] = op.payload.data;
          }
        });

        // Apply pending updates to the fresh data
        const updatedData = data.map(product => ({
          ...product,
          ...(pendingUpdates[product.id] || {}),
        }));

        setProducts(updatedData);
        await AsyncStorage.setItem('products', JSON.stringify(updatedData));

        // Track successful sync
        const duration = Date.now() - startTime;
        apiClient.trackSync('load_products', 'success', {
          count: updatedData.length,
          duration,
          source: 'api',
        });

        return updatedData;
      }

      // If offline or API call fails, load from cache
      const cachedProducts = await AsyncStorage.getItem('products');
      if (cachedProducts) {
        const parsedProducts = JSON.parse(cachedProducts);
        setProducts(parsedProducts);

        // Track cache load
        apiClient.trackSync('load_products', 'cache', {
          count: parsedProducts.length,
          source: 'cache',
        });

        return parsedProducts;
      }

      return [];
    } catch (error) {
      console.error('Error loading products:', error);

      // Log the error
      Sentry.Native.captureException(error, {
        tags: { type: 'product', action: 'load' },
        extra: { isOnline },
      });

      // Try to load from cache if API fails
      try {
        const cachedProducts = await AsyncStorage.getItem('products');
        if (cachedProducts) {
          const parsedProducts = JSON.parse(cachedProducts);
          setProducts(parsedProducts);
          return parsedProducts;
        }
      } catch (cacheError) {
        console.error('Error loading from cache:', cacheError);
      }

      throw new Error('Failed to load products. Please check your connection.');
    }
  };

  // Add a new product
  const addProduct = async product => {
    try {
      const operationId = uuidv4();

      // Track the operation
      const startTime = Date.now();

      // Add to sync queue
      await syncService.addToQueue({
        id: operationId,
        type: 'create_product',
        payload: product,
        metadata: {
          timestamp: new Date().toISOString(),
          userId: user?.id,
        },
      });

      // Optimistically update UI
      const tempId = `temp-${operationId}`;
      const tempProduct = {
        ...product,
        id: tempId,
        _status: 'pending',
        _operationId: operationId,
      };

      const updatedProducts = [...products, tempProduct];
      setProducts(updatedProducts);
      await AsyncStorage.setItem('products', JSON.stringify(updatedProducts));

      // Track the operation
      const duration = Date.now() - startTime;
      apiClient.trackSync('add_product', 'success', {
        operationId,
        duration,
        productId: tempId,
      });

      return tempId;
    } catch (error) {
      console.error('Error adding product:', error);

      // Log the error
      Sentry.Native.captureException(error, {
        tags: { type: 'product', action: 'add' },
        extra: { product },
      });

      throw new Error('Failed to add product. Please try again.');
    }
  };

  // Camera barcode scanning
  const onBarCodeRead = async scanResult => {
    const { data } = scanResult;
    setShowScanner(false);

    // Find product by barcode/SKU
    const product = products.find(p => p.sku === data || p.upc === data || p.barcode === data);

    if (product) {
      setSelectedProduct(product);
      setShowProductModal(true);
    } else {
      Alert.alert('Product Not Found', `No product found with barcode: ${data}`, [
        { text: 'OK' },
        {
          text: 'Add New Product',
          onPress: () => addNewProduct(data),
        },
      ]);
    }
  };

  // Add new product with scanned barcode
  const addNewProduct = barcode => {
    // Navigate to add product screen with pre-filled barcode
    Alert.alert(
      'Feature Coming Soon',
      'Add new product functionality will be available in the next update'
    );
  };

  // Update stock (with offline support)
  const updateStock = async () => {
    if (!selectedProduct || !stockAdjustment) return;

    const adjustment = parseInt(stockAdjustment);
    if (isNaN(adjustment)) {
      Alert.alert('Error', 'Please enter a valid number');
      return;
    }

    const stockUpdate = {
      id: Date.now(),
      productId: selectedProduct.product_id,
      adjustment: adjustment,
      timestamp: new Date().toISOString(),
      type: 'stock_update',
      synced: false,
    };

    try {
      if (isOnline) {
        // Try to sync immediately
        const response = await fetch(
          `${API_BASE_URL}/inventory/update_stock/${selectedProduct.product_id}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${authToken}`,
            },
            body: JSON.stringify({
              quantity_change: adjustment,
              notes: 'Mobile app stock update',
            }),
          }
        );

        if (response.ok) {
          // Update local product data
          const updatedProducts = products.map(p =>
            p.product_id === selectedProduct.product_id
              ? { ...p, stock_quantity: (p.stock_quantity || 0) + adjustment }
              : p
          );
          setProducts(updatedProducts);
          await AsyncStorage.setItem('products', JSON.stringify(updatedProducts));

          Alert.alert('Success', 'Stock updated successfully');
        } else {
          throw new Error('Server error');
        }
      } else {
        // Store for offline sync
        const newPending = [...pendingSync, stockUpdate];
        setPendingSync(newPending);
        await AsyncStorage.setItem('pendingSync', JSON.stringify(newPending));

        // Update local data optimistically
        const updatedProducts = products.map(p =>
          p.product_id === selectedProduct.product_id
            ? { ...p, stock_quantity: (p.stock_quantity || 0) + adjustment }
            : p
        );
        setProducts(updatedProducts);
        await AsyncStorage.setItem('products', JSON.stringify(updatedProducts));

        Alert.alert('Offline Mode', 'Stock update saved. Will sync when online.');
      }
    } catch (error) {
      // Store for offline sync on error
      const newPending = [...pendingSync, stockUpdate];
      setPendingSync(newPending);
      await AsyncStorage.setItem('pendingSync', JSON.stringify(newPending));

      Alert.alert('Sync Later', 'Update saved for later synchronization');
    }

    setShowProductModal(false);
    setStockAdjustment('');
    setSelectedProduct(null);
  };

  // Sync pending changes when back online
  const syncPendingChanges = async () => {
    if (!authToken || pendingSync.length === 0) return;

    const successfulSyncs = [];

    for (const item of pendingSync) {
      try {
        if (item.type === 'stock_update') {
          const response = await fetch(`${API_BASE_URL}/inventory/update_stock/${item.productId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${authToken}`,
            },
            body: JSON.stringify({
              quantity_change: item.adjustment,
              notes: `Mobile app sync - ${item.timestamp}`,
            }),
          });

          if (response.ok) {
            successfulSyncs.push(item.id);
          }
        }
      } catch (error) {
        console.error('Sync error for item:', item.id, error);
      }
    }

    // Remove successfully synced items
    const remainingPending = pendingSync.filter(item => !successfulSyncs.includes(item.id));
    setPendingSync(remainingPending);
    await AsyncStorage.setItem('pendingSync', JSON.stringify(remainingPending));

    if (successfulSyncs.length > 0) {
      Alert.alert('Sync Complete', `${successfulSyncs.length} items synchronized`);
      loadProducts(); // Refresh data
    }
  };

  // Request camera permission (temporarily disabled)
  const requestCameraPermission = async () => {
    // const { status } = await Camera.requestCameraPermissionsAsync();
    // return status === 'granted';
    return true; // Temporarily return true for build
  };

  // Open barcode scanner
  const openScanner = async () => {
    const hasPermission = await requestCameraPermission();
    if (hasPermission) {
      setShowScanner(true);
    } else {
      Alert.alert('Permission Denied', 'Camera permission is required to scan barcodes');
    }
  };

  // Render login screen
  if (showLogin) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle='dark-content' />
        <View style={styles.loginContainer}>
          <Text style={styles.title}>Electronics Store</Text>
          <Text style={styles.subtitle}>Mobile Inventory</Text>

          <TextInput
            style={styles.input}
            placeholder='Username'
            value={username}
            onChangeText={setUsername}
            autoCapitalize='none'
          />

          <TextInput
            style={styles.input}
            placeholder='Password'
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <TouchableOpacity style={styles.loginButton} onPress={login}>
            <Text style={styles.loginButtonText}>Login</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Render barcode scanner (temporarily disabled)
  if (showScanner) {
    return (
      <View style={styles.container}>
        <View style={styles.camera}>
          <View style={styles.scannerOverlay}>
            <Text style={styles.scannerText}>
              Camera functionality temporarily disabled for build
            </Text>
            <TouchableOpacity
              style={styles.closeScannerButton}
              onPress={() => setShowScanner(false)}
            >
              <Icon name='close' size={30} color='white' />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  // Main app interface
  return (
    <View style={styles.container}>
      <StatusBar barStyle='dark-content' />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Inventory</Text>
        <View style={styles.headerRight}>
          {!isOnline && (
            <View style={styles.offlineIndicator}>
              <Text style={styles.offlineText}>Offline</Text>
            </View>
          )}
          {pendingSync.length > 0 && (
            <View style={styles.syncIndicator}>
              <Text style={styles.syncText}>{pendingSync.length}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Action buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity style={styles.actionButton} onPress={openScanner}>
          <Icon name='qr-code-scanner' size={24} color='white' />
          <Text style={styles.actionButtonText}>Scan</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton} onPress={loadProducts}>
          <Icon name='refresh' size={24} color='white' />
          <Text style={styles.actionButtonText}>Refresh</Text>
        </TouchableOpacity>

        {pendingSync.length > 0 && isOnline && (
          <TouchableOpacity style={styles.syncButton} onPress={syncPendingChanges}>
            <Icon name='sync' size={24} color='white' />
            <Text style={styles.actionButtonText}>Sync</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Products list */}
      <FlatList
        data={products}
        keyExtractor={item => item.product_id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.productItem}
            onPress={() => {
              setSelectedProduct(item);
              setShowProductModal(true);
            }}
          >
            <View style={styles.productInfo}>
              <Text style={styles.productName}>{item.name}</Text>
              <Text style={styles.productSku}>SKU: {item.sku}</Text>
              <Text style={styles.productStock}>Stock: {item.stock_quantity || 0}</Text>
            </View>
            <View style={styles.productPrice}>
              <Text style={styles.priceText}>${item.price}</Text>
            </View>
          </TouchableOpacity>
        )}
        refreshing={false}
        onRefresh={loadProducts}
      />

      {/* Product modal */}
      <Modal visible={showProductModal} animationType='slide' transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedProduct && (
              <>
                <Text style={styles.modalTitle}>{selectedProduct.name}</Text>
                <Text style={styles.modalSku}>SKU: {selectedProduct.sku}</Text>
                <Text style={styles.modalStock}>
                  Current Stock: {selectedProduct.stock_quantity || 0}
                </Text>

                <TextInput
                  style={styles.stockInput}
                  placeholder='Stock adjustment (+/-)'
                  value={stockAdjustment}
                  onChangeText={setStockAdjustment}
                  keyboardType='numeric'
                />

                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => {
                      setShowProductModal(false);
                      setStockAdjustment('');
                      setSelectedProduct(null);
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>

                  <TouchableOpacity style={styles.updateButton} onPress={updateStock}>
                    <Text style={styles.updateButtonText}>Update</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );

  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    alignItems: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 8,
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  actionButtonText: {
    color: 'white',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
  },
  camera: {
    flex: 1,
  },
  cancelButton: {
    alignItems: 'center',
    backgroundColor: '#ccc',
    borderRadius: 8,
    flex: 1,
    marginRight: 10,
    padding: 12,
  },
  cancelButtonText: {
    color: '#333',
    fontWeight: 'bold',
  },
  closeScannerButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 25,
    padding: 10,
    position: 'absolute',
    right: 20,
    top: 50,
  },
  container: {
    backgroundColor: '#f5f5f5',
    flex: 1,
  },
  header: {
    alignItems: 'center',
    backgroundColor: 'white',
    borderBottomColor: '#eee',
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 20,
  },
  headerRight: {
    alignItems: 'center',
    flexDirection: 'row',
  },
  headerTitle: {
    color: '#333',
    fontSize: 24,
    fontWeight: 'bold',
  },
  input: {
    backgroundColor: 'white',
    borderColor: '#ddd',
    borderRadius: 8,
    borderWidth: 1,
    height: 50,
    marginBottom: 15,
    paddingHorizontal: 15,
    width: '100%',
  },
  loginButton: {
    alignItems: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 8,
    height: 50,
    justifyContent: 'center',
    width: '100%',
  },
  loginButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loginContainer: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 10,
    maxWidth: 400,
    padding: 20,
    width: '90%',
  },
  modalOverlay: {
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    flex: 1,
    justifyContent: 'center',
  },
  modalSku: {
    color: '#666',
    fontSize: 16,
    marginBottom: 5,
  },
  modalStock: {
    color: '#007AFF',
    fontSize: 16,
    marginBottom: 20,
  },
  modalTitle: {
    color: '#333',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  offlineIndicator: {
    backgroundColor: '#ff6b6b',
    borderRadius: 12,
    marginRight: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  offlineText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  priceText: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
  },
  productInfo: {
    flex: 1,
  },
  productItem: {
    backgroundColor: 'white',
    borderRadius: 8,
    elevation: 2,
    flexDirection: 'row',
    marginHorizontal: 15,
    marginVertical: 5,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  productName: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
  productPrice: {
    justifyContent: 'center',
  },
  productSku: {
    color: '#666',
    fontSize: 14,
    marginTop: 4,
  },
  productStock: {
    color: '#007AFF',
    fontSize: 14,
    marginTop: 4,
  },
  scannerOverlay: {
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    flex: 1,
    justifyContent: 'center',
  },
  scannerText: {
    color: 'white',
    fontSize: 18,
    marginBottom: 20,
    textAlign: 'center',
  },
  stockInput: {
    borderColor: '#ddd',
    borderRadius: 8,
    borderWidth: 1,
    fontSize: 16,
    marginBottom: 20,
    padding: 12,
  },
  subtitle: {
    color: '#666',
    fontSize: 18,
    marginBottom: 40,
  },
  syncButton: {
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  syncIndicator: {
    alignItems: 'center',
    backgroundColor: '#ffa726',
    borderRadius: 12,
    minWidth: 24,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  syncText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  title: {
    color: '#333',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  updateButton: {
    alignItems: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 8,
    flex: 1,
    marginLeft: 10,
    padding: 12,
  },
  updateButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
});
