import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';

const API_BASE = 'http://localhost:8000'; // Adjust for your backend IP if needed

export default function ProductListScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE}/products`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
        // Cache data
        await AsyncStorage.setItem('products', JSON.stringify(data));
      } else {
        // Load from cache
        const cached = await AsyncStorage.getItem('products');
        if (cached) {
          setProducts(JSON.parse(cached));
          Alert.alert('Offline', 'Using cached data.');
        }
      }
    } catch (error) {
      console.error(error);
      // Load from cache
      const cached = await AsyncStorage.getItem('products');
      if (cached) {
        setProducts(JSON.parse(cached));
        Alert.alert('Offline', 'Using cached data.');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderProduct = ({ item }) => (
    <TouchableOpacity
      style={styles.productItem}
      onPress={() => navigation.navigate('ProductDetail', { product: item })}
    >
      <Text style={styles.productName}>{item.name}</Text>
      <Text>Stock: {item.stock_quantity}</Text>
      <TouchableOpacity
        style={styles.updateButton}
        onPress={() => navigation.navigate('StockUpdate', { product: item })}
      >
        <Text style={styles.buttonText}>Update Stock</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={products}
        keyExtractor={item => item.product_id.toString()}
        renderItem={renderProduct}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  buttonText: {
    color: 'white',
    textAlign: 'center',
  },
  container: {
    flex: 1,
    padding: 20,
  },
  productItem: {
    borderBottomColor: '#ccc',
    borderBottomWidth: 1,
    padding: 15,
  },
  productName: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  updateButton: {
    backgroundColor: '#007bff',
    borderRadius: 5,
    marginTop: 10,
    padding: 10,
  },
});
