import { useRoute, useNavigation } from '@react-navigation/native';
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Appbar, TextInput, Button, Text, useTheme, ActivityIndicator } from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';

import { RootStackParamList } from '../navigation/types';
import { updateProductQuantity } from '../src/store/slices/productsSlice';
import { selectProductById } from '../src/store/slices/productsSlice';
import { selectIsSyncing } from '../src/store/slices/syncQueue';
import { Product } from '../types';

type StockUpdateRouteProp = RouteProp<RootStackParamList, 'StockUpdate'>;

const StockUpdateScreen = () => {
  const route = useRoute<StockUpdateRouteProp>();
  const navigation = useNavigation();
  const theme = useTheme();
  const dispatch = useDispatch();

  const { productId } = route.params;
  const [quantity, setQuantity] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const product = useSelector(state => selectProductById(state, productId)) as Product | undefined;

  const isSyncing = useSelector(selectIsSyncing);
  const isLoading = !product || isSubmitting;

  useEffect(() => {
    if (product) {
      setQuantity(product.quantity.toString());
    }
  }, [product]);

  const handleUpdateStock = async () => {
    if (!product) return;

    const newQuantity = parseInt(quantity, 10);

    if (isNaN(newQuantity)) {
      setError('Please enter a valid number');
      return;
    }

    if (newQuantity < 0) {
      setError('Quantity cannot be negative');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await dispatch(
        updateProductQuantity({
          productId: product.id,
          quantity: newQuantity,
        })
      ).unwrap();

      // Show success message
      Alert.alert('Success', 'Stock updated successfully', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (err) {
      console.error('Failed to update stock:', err);
      Alert.alert('Error', err.message || 'Failed to update stock. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!product) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size='large' color={theme.colors.primary} />
        <Text style={styles.loadingText}>Loading product information...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title='Update Stock' />
      </Appbar.Header>

      <View style={styles.content}>
        <Text style={styles.productName}>{product.name}</Text>
        <Text style={styles.currentStock}>
          Current Stock: <Text style={styles.stockValue}>{product.quantity} units</Text>
        </Text>

        <TextInput
          label='New Quantity'
          value={quantity}
          onChangeText={setQuantity}
          keyboardType='numeric'
          style={styles.input}
          disabled={isSubmitting}
          error={!!error}
        />

        {error ? <Text style={styles.errorText}>{error}</Text> : null}

        <View style={styles.buttonContainer}>
          <Button
            mode='contained'
            onPress={handleUpdateStock}
            loading={isSubmitting}
            disabled={isSubmitting || isSyncing}
            style={[styles.button, { backgroundColor: theme.colors.primary }]}
            labelStyle={styles.buttonLabel}
          >
            {isSubmitting ? 'Updating...' : 'Update Stock'}
          </Button>

          {isSyncing && !isSubmitting && (
            <View style={styles.syncingContainer}>
              <ActivityIndicator size='small' color={theme.colors.primary} />
              <Text style={styles.syncingText}>Syncing changes...</Text>
            </View>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 4,
    padding: 6,
  },
  buttonContainer: {
    marginTop: 24,
  },
  buttonLabel: {
    color: 'white',
    fontSize: 16,
  },
  centered: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  currentStock: {
    fontSize: 16,
    marginBottom: 24,
  },
  errorText: {
    color: 'red',
    marginBottom: 16,
  },
  input: {
    backgroundColor: 'white',
    marginBottom: 16,
  },
  loadingText: {
    marginTop: 16,
  },
  productName: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  stockValue: {
    fontWeight: 'bold',
  },
  syncingContainer: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  syncingText: {
    color: '#666',
    marginLeft: 8,
  },
});

export default StockUpdateScreen;
