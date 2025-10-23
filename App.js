import { Ionicons } from '@expo/vector-icons';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import * as Font from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import React, { useEffect, useState } from 'react';
import { Provider as PaperProvider, ActivityIndicator, View } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as StoreProvider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';

// Store
import ProductDetailScreen from './screens/ProductDetail';
import ProductListScreen from './screens/ProductList';
import StockUpdateScreen from './screens/StockUpdate';
import { store, persistor } from './src/store/store';

// Screens

// Theme
import { theme } from './src/theme';

// Initialize font loading
async function loadResourcesAsync() {
  await Promise.all([
    Font.loadAsync({
      ...Ionicons.font,
      // Remove missing font for now - can be added later
      // 'space-mono': require('./assets/fonts/SpaceMono-Regular.ttf'),
    }),
  ]);
}

// Keep the splash screen visible while we fetch resources
SplashScreen.preventAutoHideAsync();

const Stack = createStackNavigator();

function AppContent() {
  const [isLoadingComplete, setLoadingComplete] = useState(false);

  // Load any resources or data that we need prior to rendering the app
  useEffect(() => {
    async function loadResourcesAndDataAsync() {
      try {
        await loadResourcesAsync();
      } catch (e) {
        console.warn('Failed to load resources', e);
      } finally {
        setLoadingComplete(true);
        await SplashScreen.hideAsync();
      }
    }

    loadResourcesAndDataAsync();
  }, []);

  if (!isLoadingComplete) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size='large' />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <NavigationContainer theme={theme}>
          <Stack.Navigator
            initialRouteName='ProductList'
            screenOptions={{
              headerStyle: {
                backgroundColor: theme.colors.primary,
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            }}
          >
            <Stack.Screen
              name='ProductList'
              component={ProductListScreen}
              options={{ title: 'Inventory' }}
            />
            <Stack.Screen
              name='ProductDetail'
              component={ProductDetailScreen}
              options={{ title: 'Product Details' }}
            />
            <Stack.Screen
              name='StockUpdate'
              component={StockUpdateScreen}
              options={{ title: 'Update Stock' }}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </PaperProvider>
    </SafeAreaProvider>
  );
}

export default function App() {
  return (
    <StoreProvider store={store}>
      <PaperProvider theme={theme}>
        <SafeAreaProvider>
          <PersistGate loading={null} persistor={persistor}>
            <View testID='app-container' style={{ flex: 1 }}>
              <AppContent />
            </View>
          </PersistGate>
        </SafeAreaProvider>
      </PaperProvider>
    </StoreProvider>
  );
}
