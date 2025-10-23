#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔧 Fixing Android build issues...');

// Path to the main build.gradle file
const buildGradlePath = path.join(__dirname, 'android', 'build.gradle');
const appBuildGradlePath = path.join(__dirname, 'android', 'app', 'build.gradle');

// Fix main build.gradle
if (fs.existsSync(buildGradlePath)) {
  let buildGradleContent = fs.readFileSync(buildGradlePath, 'utf8');

  // Check if the fix is already applied
  if (!buildGradleContent.includes('androidx.camera:camera-view')) {
    console.log('📝 Applying repository and dependency resolution fixes...');

    // Add dependency substitution for cameraview
    const substitutionFix = `
    // Add dependency resolution strategy for cameraview
    configurations.all {
        resolutionStrategy {
            force 'androidx.camera:camera-core:1.3.0'
            force 'androidx.camera:camera-camera2:1.3.0'
            force 'androidx.camera:camera-lifecycle:1.3.0'
            force 'androidx.camera:camera-view:1.3.0'
        }
        
        // Replace deprecated cameraview with AndroidX Camera
        resolutionStrategy.dependencySubstitution {
            substitute module('com.google.android:cameraview') using module('androidx.camera:camera-view:1.3.0')
        }
    }`;

    // Insert before the closing brace of allprojects
    buildGradleContent = buildGradleContent.replace(/allprojects\s*\{[\s\S]*?\n\}/, match =>
      match.replace(/\n\}$/, substitutionFix + '\n}')
    );

    fs.writeFileSync(buildGradlePath, buildGradleContent);
    console.log('✅ Main build.gradle updated');
  } else {
    console.log('✅ Main build.gradle already has the fix');
  }
}

// Fix app build.gradle
if (fs.existsSync(appBuildGradlePath)) {
  let appBuildGradleContent = fs.readFileSync(appBuildGradlePath, 'utf8');

  // Check if the fix is already applied
  if (!appBuildGradleContent.includes('androidx.camera:camera-core')) {
    console.log('📝 Adding AndroidX Camera dependencies...');

    // Add AndroidX Camera dependencies
    const cameraDependencies = `
    // Fix for expo-camera cameraview dependency issue
    implementation 'androidx.camera:camera-core:1.3.0'
    implementation 'androidx.camera:camera-camera2:1.3.0'
    implementation 'androidx.camera:camera-lifecycle:1.3.0'
    implementation 'androidx.camera:camera-view:1.3.0'`;

    // Insert after react-android dependency
    appBuildGradleContent = appBuildGradleContent.replace(
      /implementation\("com\.facebook\.react:react-android"\)/,
      `implementation("com.facebook.react:react-android")${cameraDependencies}`
    );

    fs.writeFileSync(appBuildGradlePath, appBuildGradleContent);
    console.log('✅ App build.gradle updated');
  } else {
    console.log('✅ App build.gradle already has the fix');
  }
}

console.log('🎉 Android build fixes applied successfully!');
console.log('💡 You can now try running: npx expo run:android');
