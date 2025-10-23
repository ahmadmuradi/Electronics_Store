import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API_BASE = 'http://localhost:8000';

export default function StockUpdateScreen({ route, navigation }) {
  const { product } = route.params;
  const [newStock, setNewStock] = useState(product.stock_quantity.toString());

  const updateStock = async () => {
    const newStockValue = parseInt(newStock);

    // Validation
    if (isNaN(newStockValue) || newStockValue < 0) {
      Alert.alert('Error', 'Please enter a valid stock quantity (0 or greater)');
      return;
    }

    const quantityChange = newStockValue - product.stock_quantity;

    try {
      const response = await fetch(
        `${API_BASE}/inventory/update_stock/${product.product_id}?quantity_change=${quantityChange}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        Alert.alert('Success', 'Stock updated successfully!');
        await updateLocalCache(newStockValue);
        navigation.goBack();
      } else {
        const errorData = await response.json().catch(() => ({}));
        Alert.alert('Error', errorData.detail || 'Failed to update stock.');
      }
    } catch (error) {
      console.error('Stock update error:', error);
      Alert.alert('Error', 'Network error. Please try again later.');
    }
  };

  const updateLocalCache = async newStockValue => {
    try {
      const cached = await AsyncStorage.getItem('products');
      if (cached) {
        const products = JSON.parse(cached);
        const index = products.findIndex(p => p.product_id === product.product_id);
        if (index !== -1) {
          products[index].stock_quantity = newStockValue;
          await AsyncStorage.setItem('products', JSON.stringify(products));
        }
      }
    } catch (error) {
      console.error('Cache update error:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Update Stock for {product.name}</Text>
      <TextInput
        style={styles.input}
        value={newStock}
        onChangeText={setNewStock}
        keyboardType='numeric'
        placeholder='New stock quantity'
      />
      <TouchableOpacity style={styles.button} onPress={updateStock}>
        <Text style={styles.buttonText}>Update Stock</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#28a745',
    borderRadius: 5,
    padding: 15,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    textAlign: 'center',
  },
  container: {
    flex: 1,
    padding: 20,
  },
  input: {
    borderColor: '#ccc',
    borderRadius: 5,
    borderWidth: 1,
    marginBottom: 20,
    padding: 10,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
  },
});
