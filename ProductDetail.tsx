import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import {
  Appbar,
  Card,
  Title,
  Paragraph,
  Button,
  useTheme,
  ActivityIndicator,
  Text,
} from 'react-native-paper';
import { useSelector } from 'react-redux';

import { RootStackParamList } from '../navigation/types';
import { selectProductById } from '../src/store/slices/productsSlice';
import { Product } from '../types';

type ProductDetailRouteProp = RouteProp<RootStackParamList, 'ProductDetail'>;
type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'ProductDetail'>;

const ProductDetailScreen = () => {
  const route = useRoute<ProductDetailRouteProp>();
  const navigation = useNavigation<NavigationProp>();
  const { productId } = route.params;
  const theme = useTheme();

  const product = useSelector((state: any) => selectProductById(state, productId)) as
    | Product
    | undefined;

  const handleUpdateStock = () => {
    // Navigate to stock update screen
    navigation.navigate('StockUpdate', { productId });
  };

  if (!product) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size='large' color={theme.colors.primary} />
        <Paragraph style={styles.loadingText}>Loading product details...</Paragraph>
      </View>
    );
  }

  if (!product) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size='large' color={theme.colors.primary} />
        <Text style={styles.loadingText}>Loading product details...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Appbar.Header>
        <Appbar.BackAction testID='back-button' onPress={() => navigation.goBack()} />
        <Appbar.Content title='Product Details' />
      </Appbar.Header>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card style={styles.card}>
          <Card.Cover
            source={{ uri: product.imageUrl || 'https://via.placeholder.com/300' }}
            style={styles.productImage}
            testID='product-image'
          />
          <Card.Content>
            <Title style={styles.title} testID='product-name'>
              {product.name}
            </Title>
            <Paragraph style={styles.description} testID='product-description'>
              {product.description}
            </Paragraph>
            <View style={styles.detailRow}>
              <Text style={styles.price} testID='product-price'>
                ${product.price.toFixed(2)}
              </Text>
              <Text style={styles.quantity} testID='product-quantity'>
                In Stock: {product.quantity}
              </Text>
            </View>
            <View style={styles.metaContainer}>
              <Text style={styles.metaText} testID='product-sku'>
                SKU: {product.sku}
              </Text>
              <Text style={styles.metaText} testID='product-category'>
                Category: {product.category}
              </Text>
            </View>
            <Paragraph style={styles.price}>${product.price.toFixed(2)}</Paragraph>

            <View style={styles.detailRow}>
              <Paragraph style={styles.label}>SKU:</Paragraph>
              <Paragraph>{product.sku}</Paragraph>
            </View>

            <View style={styles.detailRow}>
              <Paragraph style={styles.label}>Category:</Paragraph>
              <Paragraph>{product.category}</Paragraph>
            </View>

            <View style={styles.detailRow}>
              <Paragraph style={styles.label}>Current Stock:</Paragraph>
              <Paragraph
                style={[
                  styles.stockQuantity,
                  { color: product.quantity > 0 ? theme.colors.primary : theme.colors.error },
                ]}
              >
                {product.quantity} units
              </Paragraph>
            </View>

            {product.description && (
              <View style={styles.section}>
                <Paragraph style={styles.sectionTitle}>Description</Paragraph>
                <Paragraph>{product.description}</Paragraph>
              </View>
            )}

            <View style={styles.section}>
              <Paragraph style={styles.sectionTitle}>Last Updated</Paragraph>
              <Paragraph>{new Date(product.lastUpdated).toLocaleString()}</Paragraph>
            </View>
          </Card.Content>

          <Card.Actions style={styles.actions}>
            <Button
              mode='contained'
              onPress={handleUpdateStock}
              style={[styles.button, { backgroundColor: theme.colors.primary }]}
              labelStyle={styles.buttonLabel}
            >
              Update Stock
            </Button>
          </Card.Actions>
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  actions: {
    justifyContent: 'flex-end',
    padding: 16,
  },
  button: {
    borderRadius: 4,
  },
  buttonLabel: {
    color: 'white',
  },
  card: {
    marginBottom: 16,
  },
  card: {
    borderRadius: 8,
    overflow: 'hidden',
  },
  centered: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    padding: 20,
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
  description: {
    color: '#666',
    fontSize: 16,
    marginBottom: 16,
  },
  detailRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: {
    fontWeight: 'bold',
    width: '40%',
  },
  loadingText: {
    marginTop: 16,
  },
  loadingText: {
    marginTop: 16,
  },
  metaContainer: {
    marginTop: 8,
  },
  metaText: {
    color: '#757575',
    fontSize: 14,
    marginBottom: 4,
  },
  price: {
    color: '#2196F3',
    fontSize: 22,
    fontWeight: 'bold',
  },
  price: {
    color: '#2e7d32',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  productImage: {
    height: 300,
  },
  productImage: {
    height: 300,
  },
  quantity: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '500',
  },
  scrollContent: {
    padding: 16,
  },
  scrollContent: {
    padding: 16,
  },
  section: {
    borderTopColor: '#e0e0e0',
    borderTopWidth: 1,
    marginTop: 16,
    paddingTop: 16,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
  },
  stockQuantity: {
    fontWeight: 'bold',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
});

export default ProductDetailScreen;
