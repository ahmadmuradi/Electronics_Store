import { useNavigation } from '@react-navigation/native';
import React, { useEffect } from 'react';
import { View, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import { Card, Title, Paragraph, Button, useTheme } from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';

import { fetchProductsList } from '../src/store/slices/productsSlice';
import { selectAllProducts, selectProductsStatus } from '../src/store/slices/productsSlice';
import { selectIsSyncing } from '../src/store/slices/syncQueue';
import { AppState } from '../src/store/store';
import { Product } from '../src/types';

type ProductItemProps = {
  product: Product;
  onPress: () => void;
  onUpdateStock: () => void;
};

const ProductItem = React.memo(({ product, onPress, onUpdateStock }: ProductItemProps) => {
  const theme = useTheme();

  return (
    <Card style={styles.card} onPress={onPress}>
      <Card.Content>
        <Title>{product.name}</Title>
        <Paragraph>SKU: {product.sku}</Paragraph>
        <Paragraph>Stock: {product.quantity}</Paragraph>
        <Paragraph>${product.price.toFixed(2)}</Paragraph>
      </Card.Content>
      <Card.Actions>
        <Button
          mode='contained'
          onPress={onUpdateStock}
          style={[styles.button, { backgroundColor: theme.colors.primary }]}
        >
          Update Stock
        </Button>
      </Card.Actions>
    </Card>
  );
});

const ProductListScreen = () => {
  const navigation = useNavigation();
  const dispatch = useDispatch();
  const products = useSelector(selectAllProducts);
  const { status, error } = useSelector(selectProductsStatus);
  const isSyncing = useSelector(selectIsSyncing);
  const theme = useTheme();

  useEffect(() => {
    dispatch(fetchProductsList());
  }, [dispatch]);

  const handleProductPress = (productId: string) => {
    navigation.navigate('ProductDetail', { productId });
  };

  const handleUpdateStock = (productId: string) => {
    navigation.navigate('StockUpdate', { productId });
  };

  if (status === 'loading' && products.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size='large' color={theme.colors.primary} />
      </View>
    );
  }

  if (status === 'failed') {
    return (
      <View style={styles.centered}>
        <Paragraph style={styles.error}>Error loading products: {error}</Paragraph>
        <Button
          mode='contained'
          onPress={() => dispatch(fetchProductsList())}
          style={styles.retryButton}
        >
          Retry
        </Button>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <FlatList
        data={products}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <ProductItem
            product={item}
            onPress={() => handleProductPress(item.id)}
            onUpdateStock={() => handleUpdateStock(item.id)}
          />
        )}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.centered}>
            <Paragraph>No products found</Paragraph>
          </View>
        }
        refreshControl={
          <RefreshControl
            refreshing={isSyncing}
            onRefresh={() => dispatch(fetchProductsList())}
            colors={[theme.colors.primary]}
          />
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  button: {
    marginTop: 8,
  },
  card: {
    elevation: 2,
    marginBottom: 16,
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
  error: {
    color: 'red',
    marginBottom: 16,
    textAlign: 'center',
  },
  listContent: {
    padding: 16,
  },
  retryButton: {
    marginTop: 16,
  },
});

export default ProductListScreen;
