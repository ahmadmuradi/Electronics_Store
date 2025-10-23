// Global mocks and setup
import '@testing-library/jest-native/extend-expect';

// Mock React Native modules
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
jest.mock('react-native/Libraries/Animated/NativeAnimatedModule');

// Mock AsyncStorage
const mockAsyncStorage = require('@react-native-async-storage/async-storage/jest/async-storage-mock');
jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);

// Mock NetInfo
const mockNetInfo = {
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
  useNetInfo: jest.fn(() => ({
    isConnected: true,
    isInternetReachable: true,
  })),
};
jest.mock('@react-native-community/netinfo', () => mockNetInfo);

// Mock Expo modules
jest.mock('expo-camera', () => ({
  Camera: {
    requestCameraPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
  },
}));

jest.mock('expo-barcode-scanner', () => ({
  BarCodeScanner: {
    Constants: {
      BarCodeType: {
        qr: 'qr',
        ean13: 'ean13',
      },
    },
  },
}));

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');

// Mock React Navigation
const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  addListener: jest.fn((event, callback) => {
    callback();
    return jest.fn();
  }),
  isFocused: jest.fn().mockReturnValue(true),
  setOptions: jest.fn(),
  dispatch: jest.fn(),
  reset: jest.fn(),
  canGoBack: jest.fn().mockReturnValue(true),
  getParent: jest.fn(),
  getState: jest.fn(),
};

jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => mockNavigation,
  useRoute: () => ({
    params: {},
    name: 'MockScreen',
    key: 'MockScreen',
  }),
  useFocusEffect: jest.fn(),
  useIsFocused: jest.fn().mockReturnValue(true),
  NavigationContainer: ({ children }) => children,
}));

jest.mock('@react-navigation/stack', () => ({
  createStackNavigator: () => ({
    Navigator: ({ children }) => children,
    Screen: ({ children }) => children,
  }),
}));

// Mock Expo SecureStore
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock React Native Paper
jest.mock('react-native-paper', () => {
  const RealComponent = jest.requireActual('react-native-paper');
  return {
    ...RealComponent,
    Portal: ({ children }) => children,
    Modal: ({ children, visible, onDismiss }) => (visible ? children : null),
  };
});

// Global fetch mock
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  })
);

// Mock timers
jest.useFakeTimers();

// Mock React Native's Animated
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock Dimensions
jest.mock('react-native/Libraries/Utilities/Dimensions', () => ({
  get: jest.fn().mockReturnValue({ width: 375, height: 667, scale: 1, fontScale: 1 }),
  set: jest.fn(),
}));

// Mock Platform
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'ios',
  select: objs => objs.ios,
}));

// Mock React Native's Keyboard
jest.mock('react-native/Libraries/Components/Keyboard/Keyboard', () => ({
  addListener: jest.fn(),
  removeListener: jest.fn(),
  dismiss: jest.fn(),
}));

// Mock React Native's AppState
jest.mock('react-native/Libraries/AppState/AppState', () => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  currentState: 'active',
}));

// Mock React Native's BackHandler
jest.mock('react-native/Libraries/Utilities/BackHandler', () => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

// Mock React Native's Linking
jest.mock('react-native/Libraries/Linking/Linking', () => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  openURL: jest.fn(),
  canOpenURL: jest.fn(),
  getInitialURL: jest.fn(),
  openSettings: jest.fn(),
  sendIntent: jest.fn(),
}));

// Mock React Native's Alert
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

// Mock React Native's PixelRatio
jest.mock('react-native/Libraries/Utilities/PixelRatio', () => ({
  get: jest.fn().mockReturnValue(2),
  getFontScale: jest.fn().mockReturnValue(1),
  getPixelSizeForLayoutSize: jest.fn().mockImplementation(size => Math.round(size * 2)),
  roundToNearestPixel: jest.fn().mockImplementation(size => Math.round(size * 2) / 2),
}));

// Mock React Native's StyleSheet
jest.mock('react-native/Libraries/StyleSheet/StyleSheet', () => {
  const RealStyleSheet = jest.requireActual('react-native/Libraries/StyleSheet/StyleSheet');
  return {
    ...RealStyleSheet,
    hairlineWidth: 1,
  };
});

// Mock React Native's UIManager
jest.mock('react-native/Libraries/ReactNative/UIManager', () => ({
  getViewManagerConfig: jest.fn(),
  hasViewManagerConfig: jest.fn(),
  createView: jest.fn(),
  dispatchViewManagerCommand: jest.fn(),
  getViewManagerConfig: jest.fn(() => ({
    Commands: {},
  })),
  hasViewManagerConfig: jest.fn(() => true),
  getConstantsForViewManager: jest.fn(),
  getDefaultEventTypes: jest.fn(),
  AndroidDrawerLayout: { Constants: {} },
  AndroidSwipeRefreshLayout: { Constants: {} },
  AndroidTextInput: { Commands: {} },
  ModalFullscreenView: { Constants: {} },
  RCTScrollView: { NativeProps: {} },
  RCTText: { NativeProps: {} },
  RCTView: { NativeProps: {} },
  ScrollView: { Constants: {} },
  View: { Constants: {} },
}));

// Mock React Native's NativeModules
jest.mock('react-native/Libraries/BatchedBridge/NativeModules', () => ({
  UIManager: {
    RCTView: () => ({}),
  },
  RNGestureHandlerModule: {
    attachGestureHandler: jest.fn(),
    createGestureHandler: jest.fn(),
    dropGestureHandler: jest.fn(),
    updateGestureHandler: jest.fn(),
    State: { BEGAN: 'BEGAN', FAILED: 'FAILED', ACTIVE: 'ACTIVE', CANCELLED: 'CANCELLED' },
    Direction: { RIGHT: 1, LEFT: 2, UP: 4, DOWN: 8 },
  },
  PlatformConstants: {
    forceTouchAvailable: false,
  },
}));

// Mock React Native's I18nManager
jest.mock('react-native/Libraries/ReactNative/I18nManager', () => ({
  isRTL: false,
  allowRTL: jest.fn(),
  forceRTL: jest.fn(),
  swapLeftAndRightInRTL: jest.fn(),
}));

// Mock React Native's NativeEventEmitter
jest.mock('react-native/Libraries/EventEmitter/NativeEventEmitter');

// Mock Alert
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  RN.Alert = {
    alert: jest.fn(),
  };
  return RN;
});
