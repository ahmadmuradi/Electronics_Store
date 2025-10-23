// Mock React Native
const mockNativeModules = {
  ExponentConstants: {
    appOwnership: 'expo',
    manifest: {
      extra: {
        eas: { projectId: 'test-project-id' },
        apiUrl: 'http://test-api-url',
        sentryDsn: 'test-sentry-dsn',
      },
    },
  },
};

// Mock React Native
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');

  // Mocked modules that would normally be native
  RN.NativeModules = {
    ...RN.NativeModules,
    ...mockNativeModules,
  };

  // Mock Platform
  const platform = {
    ...RN.Platform,
    OS: 'ios',
    select: objs => objs.ios || objs.default,
  };

  return {
    ...RN,
    Platform: platform,
    NativeModules: {
      ...RN.NativeModules,
      ...mockNativeModules,
    },
  };
});

// Mock expo-constants
jest.mock('expo-constants', () => ({
  default: {
    manifest: {
      extra: {
        eas: { projectId: 'test-project-id' },
        apiUrl: 'http://test-api-url',
        sentryDsn: 'test-sentry-dsn',
      },
      version: '1.0.0',
      updates: {
        enabled: true,
        fallbackToCacheTimeout: 0,
        checkAutomatically: 'ON_LOAD',
      },
      assetBundlePatterns: ['**/*'],
    },
    appOwnership: 'expo',
    expoConfig: {
      name: 'Electronics Store',
      slug: 'electronics-store',
      version: '1.0.0',
    },
  },
}));

// Mock sentry-expo
jest.mock('sentry-expo', () => ({
  Native: {
    addBreadcrumb: jest.fn(),
    captureException: jest.fn(),
    init: jest.fn(),
  },
}));

// Mock @react-navigation/native
const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
};

const mockRoute = {
  params: { productId: '1' },
};

jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => mockNavigation,
  useRoute: () => mockRoute,
}));

// Mock AsyncStorage
const mockAsyncStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
};

jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);

// Mock react-native-safe-area-context
const insets = { top: 0, right: 0, bottom: 0, left: 0 };
const frame = { x: 0, y: 0, width: 0, height: 0 };

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  const { View } = require('react-native');

  return {
    useSafeAreaInsets: jest.fn(() => insets),
    useSafeAreaFrame: jest.fn(() => frame),
    SafeAreaProvider: jest.fn(({ children }) => children),
    SafeAreaConsumer: jest.fn(({ children }) => children(insets)),
    SafeAreaView: jest.fn(({ children, ...props }) => <View {...props}>{children}</View>),
    initialWindowMetrics: {
      frame: frame,
      insets: insets,
    },
  };
});

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
}));

// Mock react-navigation
jest.mock('@react-navigation/native', () => {
  const actualNav = jest.requireActual('@react-navigation/native');
  return {
    ...actualNav,
    useNavigation: () => ({
      navigate: jest.fn(),
      goBack: jest.fn(),
      addListener: jest.fn(),
    }),
  };
});

// Mock react-native-vector-icons
jest.mock('@expo/vector-icons', () => ({
  Ionicons: '',
}));

// Mock expo-font
jest.mock('expo-font');

// Mock expo-splash-screen
jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn(),
  hideAsync: jest.fn(),
}));

// Silence the warning: Animated: `useNativeDriver` is not supported
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');

  // The mock for `call` immediately calls the callback which is incorrect
  // So we override it for empty initialization
  return {
    ...Reanimated,
    call: () => {},
  };
});

// Mock vector icons
jest.mock('react-native-vector-icons/MaterialCommunityIcons', () => 'Icon');
jest.mock('react-native-vector-icons/Ionicons', () => 'Ionicons');

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => ({
  ...jest.requireActual('react-native-reanimated/mock'),
  default: {
    ...jest.requireActual('react-native-reanimated/mock').default,
    call: () => {},
  },
}));

// Mock @react-native-community/netinfo
jest.mock('@react-native-community/netinfo', () => ({
  fetch: jest.fn(() =>
    Promise.resolve({
      isConnected: true,
      isInternetReachable: true,
    })
  ),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  useNetInfo: () => ({
    isConnected: true,
    isInternetReachable: true,
  }),
}));

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(() => Promise.resolve('mocked-token')),
  setItemAsync: jest.fn(() => Promise.resolve()),
  deleteItemAsync: jest.fn(() => Promise.resolve()),
}));

// Mock other Expo modules
jest.mock('expo-font', () => ({
  loadAsync: jest.fn(() => Promise.resolve()),
}));

jest.mock('expo-splash-screen', () => ({
  hideAsync: jest.fn(() => Promise.resolve()),
  preventAutoHideAsync: jest.fn(() => Promise.resolve()),
}));

// Mock expo-task-manager
jest.mock('expo-task-manager', () => ({
  defineTask: jest.fn(),
  isAvailableAsync: jest.fn(() => Promise.resolve(true)),
  isTaskRegisteredAsync: jest.fn(() => Promise.resolve(false)),
  registerTaskAsync: jest.fn(() => Promise.resolve()),
  unregisterTaskAsync: jest.fn(() => Promise.resolve()),
  getTaskOptionsAsync: jest.fn(() => Promise.resolve({})),
  getRegisteredTasksAsync: jest.fn(() => Promise.resolve([])),
}));

// Mock expo-background-fetch
jest.mock('expo-background-fetch', () => ({
  setMinimumIntervalAsync: jest.fn(() => Promise.resolve()),
  getStatusAsync: jest.fn(() => Promise.resolve(1)), // 1 = BackgroundFetch.Status.Available
  registerTaskAsync: jest.fn(() => Promise.resolve()),
  unregisterTaskAsync: jest.fn(() => Promise.resolve()),
}));

// Mock expo-notifications
jest.mock('expo-notifications', () => ({
  setNotificationHandler: jest.fn(),
  getPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
  requestPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
  scheduleNotificationAsync: jest.fn(() => Promise.resolve('test-notification-id')),
  cancelScheduledNotificationAsync: jest.fn(() => Promise.resolve()),
  dismissAllNotificationsAsync: jest.fn(() => Promise.resolve()),
  getExpoPushTokenAsync: jest.fn(() => Promise.resolve({ data: 'test-push-token' })),
  addNotificationReceivedListener: jest.fn(),
  addNotificationResponseReceivedListener: jest.fn(),
  removeNotificationSubscription: jest.fn(),
  setNotificationChannelAsync: jest.fn(() => Promise.resolve()),
  getNotificationChannelsAsync: jest.fn(() => Promise.resolve([])),
}));

// Mock the config module
jest.mock('./src/config/config', () => ({
  config: {
    API_URL: 'http://test-api-url',
    SENTRY_DSN: 'test-sentry-dsn',
  },
}));

// Mock react-native-paper components
const React = require('react');
const { View, Text, TouchableOpacity } = require('react-native');

const mockPaper = {
  Provider: ({ children }) => <View testID='paper-provider'>{children}</View>,
  Appbar: {
    Header: ({ children, ...props }) => (
      <View testID='appbar-header' {...props}>
        {children}
      </View>
    ),
    Content: ({ children, ...props }) => (
      <View testID='appbar-content' {...props}>
        {children}
      </View>
    ),
    Action: ({ icon, ...props }) => (
      <View testID='appbar-action' {...props}>
        {icon}
      </View>
    ),
    BackAction: props => <View testID='appbar-back' {...props} />,
  },
  Button: ({ children, onPress, ...props }) => (
    <TouchableOpacity testID='paper-button' onPress={onPress} {...props}>
      <Text>{children}</Text>
    </TouchableOpacity>
  ),
  Card: ({ children, ...props }) => (
    <View testID='paper-card' {...props}>
      {children}
    </View>
  ),
  Card: ({ children, ...props }) => (
    <View testID='paper-card' {...props}>
      {children}
    </View>
  ),
  Title: ({ children, ...props }) => (
    <Text testID='paper-title' {...props}>
      {children}
    </Text>
  ),
  Paragraph: ({ children, ...props }) => (
    <Text testID='paper-paragraph' {...props}>
      {children}
    </Text>
  ),
  ActivityIndicator: () => <View testID='paper-activity-indicator' />,
  useTheme: () => ({
    colors: {
      primary: '#6200ee',
      background: '#ffffff',
      surface: '#ffffff',
      text: '#000000',
    },
  }),
};

jest.mock('react-native-paper', () => mockPaper);

// Mock react-native-gesture-handler
jest.mock('react-native-gesture-handler', () => {
  const View = require('react-native').View;
  return {
    ScrollView: View,
    State: {},
    FlatList: View,
    gestureHandlerRootHOC: jest.fn(component => component),
    Directions: {},
    // Add other gesture handler components as needed
    Swipeable: View,
    DrawerLayout: View,
    TouchableOpacity: View,
    TouchableHighlight: View,
    TouchableWithoutFeedback: View,
    RectButton: View,
    BorderlessButton: View,
    LongPressGestureHandler: View,
    PanGestureHandler: View,
    PinchGestureHandler: View,
    RotationGestureHandler: View,
    FlingGestureHandler: View,
    TapGestureHandler: View,
    ForceTouchGestureHandler: View,
    NativeViewGestureHandler: View,
    createNativeWrapper: jest.fn(component => component),
  };
});

// Mock for react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialCommunityIcons', () => 'Icon');
jest.mock('react-native-vector-icons/Ionicons', () => 'Ionicons');

// Silence the warning: Animated: `useNativeDriver` is not supported
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
