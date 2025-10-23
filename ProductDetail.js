import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ProductDetailScreen({ route }) {
  const { product } = route.params;

  if (!product) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>Product data not available</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{product.name}</Text>
      <Text>Description: {product.description || 'N/A'}</Text>
      <Text>Price: ${product.price}</Text>
      <Text>Stock: {product.stock_quantity}</Text>
      <Text>SKU: {product.sku || 'N/A'}</Text>
      <Text>UPC: {product.upc || 'N/A'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  error: {
    color: 'red',
    fontSize: 18,
    marginTop: 50,
    textAlign: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
});
