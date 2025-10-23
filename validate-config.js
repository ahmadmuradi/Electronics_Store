#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Expo project configuration...\n');

// Check 1: .gitignore includes .expo/
const gitignorePath = path.join(__dirname, '.gitignore');
if (fs.existsSync(gitignorePath)) {
  const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
  if (gitignoreContent.includes('.expo/')) {
    console.log('✅ .gitignore correctly excludes .expo/ directory');
  } else {
    console.log('❌ .gitignore missing .expo/ entry');
  }
} else {
  console.log('❌ .gitignore file not found');
}

// Check 2: app.json configuration
const appJsonPath = path.join(__dirname, 'app.json');
if (fs.existsSync(appJsonPath)) {
  const appJson = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));
  const expo = appJson.expo;

  // Check for native config properties that shouldn't be there
  const hasAndroidFolder = fs.existsSync(path.join(__dirname, 'android'));
  const hasIosFolder = fs.existsSync(path.join(__dirname, 'ios'));

  if (hasAndroidFolder || hasIosFolder) {
    const problematicProps = [];
    if (expo.orientation) problematicProps.push('orientation');
    if (expo.userInterfaceStyle) problematicProps.push('userInterfaceStyle');
    if (expo.ios) problematicProps.push('ios');
    if (expo.android) problematicProps.push('android');
    if (expo.plugins) problematicProps.push('plugins');

    if (problematicProps.length > 0) {
      console.log(
        `❌ app.json contains native config properties that won't be synced: ${problematicProps.join(
          ', '
        )}`
      );
    } else {
      console.log('✅ app.json correctly excludes native configuration properties');
    }
  }
} else {
  console.log('❌ app.json file not found');
}

// Check 3: Android API level
const androidBuildGradlePath = path.join(__dirname, 'android', 'build.gradle');
if (fs.existsSync(androidBuildGradlePath)) {
  const buildGradleContent = fs.readFileSync(androidBuildGradlePath, 'utf8');

  // Extract targetSdkVersion
  const targetSdkMatch = buildGradleContent.match(/targetSdkVersion.*?(\d+)/);
  if (targetSdkMatch) {
    const targetSdk = parseInt(targetSdkMatch[1]);
    if (targetSdk >= 34) {
      console.log(
        `✅ Android targetSdkVersion is ${targetSdk} (meets Google Play Store requirement)`
      );
    } else {
      console.log(
        `❌ Android targetSdkVersion is ${targetSdk} (needs to be 34+ for Google Play Store)`
      );
    }
  }

  // Extract compileSdkVersion
  const compileSdkMatch = buildGradleContent.match(/compileSdkVersion.*?(\d+)/);
  if (compileSdkMatch) {
    const compileSdk = parseInt(compileSdkMatch[1]);
    if (compileSdk >= 34) {
      console.log(`✅ Android compileSdkVersion is ${compileSdk}`);
    } else {
      console.log(`❌ Android compileSdkVersion is ${compileSdk} (should be 34+)`);
    }
  }
} else {
  console.log('❌ android/build.gradle file not found');
}

// Check 4: Package.json Expo SDK version
const packageJsonPath = path.join(__dirname, 'package.json');
if (fs.existsSync(packageJsonPath)) {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const expoVersion = packageJson.dependencies?.expo;

  if (expoVersion) {
    console.log(`✅ Expo SDK version: ${expoVersion}`);

    // Check if it's version 50+
    const versionMatch = expoVersion.match(/(\d+)/);
    if (versionMatch && parseInt(versionMatch[1]) >= 50) {
      console.log('✅ Expo SDK version supports Android API level 34');
    } else {
      console.log('⚠️  Expo SDK version may not support Android API level 34');
    }
  } else {
    console.log('❌ Expo SDK not found in dependencies');
  }
} else {
  console.log('❌ package.json file not found');
}

console.log('\n🎯 Validation complete!');
