'use strict';

module.exports = {
  preset: 'jest-expo',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  // Transform settings
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': [
      'babel-jest',
      {
        presets: [
          '@babel/preset-env',
          '@babel/preset-react',
          '@babel/preset-typescript',
          'module:metro-react-native-babel-preset',
        ],
        plugins: ['@babel/plugin-transform-runtime', 'react-native-reanimated/plugin'],
      },
    ],
  },

  // Ignore node_modules except for specific packages
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native|@react-native|react-native|@react-navigation|expo(n)?|@expo(n)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|@react-native-community|@react-native-async-storage|@react-native-picker)',
  ],

  // Setup files
  setupFiles: ['./jest.setup.js', './node_modules/react-native-gesture-handler/jestSetup.js'],

  setupFilesAfterEnv: [
    '@testing-library/jest-native/extend-expect',
    './node_modules/react-native-gesture-handler/jestSetup.js',
  ],

  // Test environment
  testEnvironment: 'jsdom',

  // Module name mapper
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^react-native$': 'react-native-web',
    '^@react-native-async-storage/async-storage$':
      '@react-native-async-storage/async-storage/jest/async-storage-mock',
    '^uuid$': require.resolve('uuid'),
    '^expo-font$': '<rootDir>/__mocks__/expo-font.js',
    '^expo-splash-screen$': '<rootDir>/__mocks__/expo-splash-screen.js',
    '^@expo/vector-icons': '<rootDir>/__mocks__/@expo/vector-icons.js',
    '^react-native-safe-area-context$': '<rootDir>/__mocks__/react-native-safe-area-context.js',
    '^@react-navigation/native$': '<rootDir>/__mocks__/@react-navigation/native.js',
    '^@react-navigation/stack$': '<rootDir>/__mocks__/@react-navigation/stack.js',
    '^react-native-reanimated$': '<rootDir>/node_modules/react-native-reanimated/mock',
  },

  // Global variables
  globals: {
    __DEV__: true,
  },

  // Add support for ES modules
  extensionsToTreatAsEsm: ['.jsx', '.ts', '.tsx'],

  // Coverage settings
  collectCoverage: false,
  collectCoverageFrom: [
    '**/*.{js,jsx,ts,tsx}',
    '!**/coverage/**',
    '!**/node_modules/**',
    '!**/babel.config.js',
    '!**/jest.setup.js',
    '!**/jest-preset.js',
  ],

  // Test timeout
  testTimeout: 30000,
};
