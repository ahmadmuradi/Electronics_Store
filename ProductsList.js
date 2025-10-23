import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';

import {
  fetchProductsList,
  selectAllProducts,
  selectProductsStatus,
} from '../store/slices/productsSlice';
import { setupNetworkListeners } from '../store/slices/productsSlice';

const ProductsList = () => {
  const dispatch = useDispatch();
  const products = useSelector(selectAllProducts);
  const { status, error, isOnline, pendingSyncCount } = useSelector(selectProductsStatus);

  // Initialize network listeners and load products
  useEffect(() => {
    // Set up network status listeners
    const unsubscribe = dispatch(setupNetworkListeners());

    // Initial data load
    dispatch(fetchProductsList());

    // Cleanup function
    return () => {
      if (unsubscribe && typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [dispatch]);

  // Handle refresh
  const handleRefresh = () => {
    dispatch(fetchProductsList(true)); // Force refresh
  };

  // Render product item
  const renderProductItem = ({ item }) => (
    <View style={styles.productItem}>
      <Text style={styles.productName}>{item.name}</Text>
      <Text>Price: ${item.price}</Text>
      <Text>
        Stock: {item.stock_quantity} {item.pendingSync && ' (Pending Sync)'}
      </Text>
      <View style={styles.quantityControls}>
        <TouchableOpacity
          style={styles.quantityButton}
          onPress={() => handleUpdateQuantity(item.id, -1, item.stock_quantity)}
        >
          <Text>-</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quantityButton}
          onPress={() => handleUpdateQuantity(item.id, 1, item.stock_quantity)}
        >
          <Text>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  // Handle quantity updates
  const handleUpdateQuantity = (productId, change, currentQuantity) => {
    const newQuantity = Math.max(0, currentQuantity + change);
    if (newQuantity !== currentQuantity) {
      dispatch(updateProductQuantity({ productId, quantity: newQuantity }));
    }
  };

  // Loading state
  if (status === 'loading' && products.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size='large' />
      </View>
    );
  }

  // Error state
  if (status === 'failed') {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Error: {error?.message || 'Failed to load products'}</Text>
        <TouchableOpacity onPress={handleRefresh} style={styles.retryButton}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Products</Text>
        {!isOnline && (
          <Text style={styles.offlineText}>
            Offline Mode{pendingSyncCount > 0 && ` • ${pendingSyncCount} pending changes`}
          </Text>
        )}
        <TouchableOpacity onPress={handleRefresh}>
          <Text style={styles.refreshText}>⟳ Refresh</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={products}
        renderItem={renderProductItem}
        keyExtractor={item => item.id.toString()}
        refreshing={status === 'loading' && products.length > 0}
        onRefresh={handleRefresh}
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  centered: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  container: {
    backgroundColor: '#f5f5f5',
    flex: 1,
  },
  errorText: {
    color: '#e74c3c',
    marginBottom: 16,
    textAlign: 'center',
  },
  header: {
    backgroundColor: '#fff',
    borderBottomColor: '#ddd',
    borderBottomWidth: 1,
    padding: 16,
  },
  listContent: {
    padding: 8,
  },
  offlineText: {
    color: '#e74c3c',
    marginBottom: 8,
  },
  productItem: {
    backgroundColor: '#fff',
    borderRadius: 8,
    elevation: 2,
    marginBottom: 8,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  productName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  quantityButton: {
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    borderRadius: 15,
    height: 30,
    justifyContent: 'center',
    marginLeft: 8,
    width: 30,
  },
  quantityControls: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
  },
  refreshText: {
    color: '#3498db',
    textAlign: 'right',
  },
  retryButton: {
    backgroundColor: '#3498db',
    borderRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  retryText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
});

export default ProductsList;
