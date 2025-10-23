const fs = require('fs');

console.log('🔧 Fixing package.json syntax...');

try {
  // Read the current package.json
  const packageJsonPath = './package.json';
  let content = fs.readFileSync(packageJsonPath, 'utf8');

  // Remove any duplicate content after the main JSON object
  // Look for the closing brace and remove everything after it
  const mainJsonEnd = content.lastIndexOf('}');
  if (mainJsonEnd !== -1 && mainJsonEnd < content.length - 2) {
    console.log('Found extra content after main JSON object, trimming...');
    content = content.substring(0, mainJsonEnd + 1);
  }

  // Parse to validate JSON is now valid
  const packageData = JSON.parse(content);

  // Write back clean package.json
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageData, null, 2));

  console.log('✅ package.json fixed successfully!');
  console.log('📦 Valid package.json structure restored');
} catch (error) {
  console.error('❌ Failed to fix package.json:', error.message);

  // Create a fresh package.json as fallback
  console.log('🔄 Creating fresh package.json...');
  const freshPackageJson = {
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
      'clean:deep': 'rm -rf node_modules package-lock.json && npm cache clean --force',
      'fix:package': 'node fix-package-json.js',
    },
    dependencies: {
      '@react-native-async-storage/async-storage': '1.21.0',
      '@react-native-community/netinfo': '11.1.0',
      '@react-navigation/native': '^6.1.9',
      '@react-navigation/stack': '^6.3.20',
      expo: '~50.0.0',
      'expo-camera': '~14.1.3',
      react: '^18.2.0',
      'react-native': '^0.73.6',
    },
    devDependencies: {
      '@babel/core': '^7.20.0',
      jest: '^29.2.1',
    },
    private: true,
  };

  fs.writeFileSync('./package.json', JSON.stringify(freshPackageJson, null, 2));
  console.log('✅ Fresh package.json created!');
}
