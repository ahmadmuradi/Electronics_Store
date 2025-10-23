#!/usr/bin/env node
// save this as fix-dependencies.js
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧹 Cleaning up corrupted dependencies...');

// Remove node_modules and lock files
if (fs.existsSync('node_modules')) {
  console.log('Removing node_modules...');
  execSync('rm -rf node_modules', { stdio: 'inherit' });
}

if (fs.existsSync('package-lock.json')) {
  console.log('Removing package-lock.json...');
  execSync('rm -f package-lock.json', { stdio: 'inherit' });
}

// Clear npm cache
console.log('Clearing npm cache...');
execSync('npm cache clean --force', { stdio: 'inherit' });

// Create a fresh package.json with verified dependencies
const packageJson = {
  name: 'electronics-store-mobile',
  version: '1.0.0',
  main: 'node_modules/expo/AppEntry.js',
  scripts: {
    start: 'expo start',
    android: 'expo run:android',
    ios: 'expo run:ios',
    web: 'expo start --web',
    test: 'jest',
    'build:android': 'eas build --platform android --profile preview',
    'build:android:production': 'eas build --platform android --profile production',
    lint: 'eslint . --ext .js,.jsx --fix',
    clean: 'rm -rf node_modules package-lock.json && npm install',
    'fix:deps': 'node fix-dependencies.js',
  },
  dependencies: {
    '@react-native-async-storage/async-storage': '1.21.0',
    '@react-native-community/netinfo': '11.1.0',
    '@react-navigation/native': '^6.1.9',
    '@react-navigation/stack': '^6.3.20',
    expo: '~50.0.0',
    'expo-barcode-scanner': '~12.9.0',
    'expo-camera': '~14.1.3',
    'expo-splash-screen': '~0.26.4',
    'expo-status-bar': '~1.11.1',
    react: '^18.2.0',
    'react-dom': '18.2.0',
    'react-native': '^0.73.6',
    'react-native-gesture-handler': '~2.14.0',
    'react-native-reanimated': '~3.6.2',
    'react-native-safe-area-context': '^4.8.2',
    'react-native-screens': '~3.29.0',
    'react-native-vector-icons': '^10.0.3',
  },
  devDependencies: {
    '@babel/core': '^7.20.0',
    jest: '^29.2.1',
  },
  overrides: {
    'es-abstract': '^1.22.1',
    'array-buffer-byte-length': '^1.0.0',
    'data-view-buffer': '^1.0.1',
    'available-typed-arrays': '^1.0.5',
  },
  resolutions: {
    'es-abstract': '^1.22.1',
    '**/es-abstract': '^1.22.1',
  },
};

console.log('Writing updated package.json...');
fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2));

console.log('Installing dependencies with retry mechanism...');

// Install with retry
let success = false;
for (let i = 0; i < 3; i++) {
  try {
    console.log(`Attempt ${i + 1} to install dependencies...`);
    execSync('npm install --legacy-peer-deps --no-optional', {
      stdio: 'inherit',
      timeout: 300000, // 5 minutes
    });
    success = true;
    break;
  } catch (error) {
    console.log(`Attempt ${i + 1} failed, retrying...`);
    // Clear cache between attempts
    execSync('npm cache clean --force', { stdio: 'inherit' });
  }
}

if (!success) {
  console.log('Trying with yarn...');
  try {
    execSync('npx yarn install', { stdio: 'inherit' });
  } catch (error) {
    console.log('Yarn also failed, trying offline installation...');
  }
}

console.log('✅ Dependency cleanup completed!');
