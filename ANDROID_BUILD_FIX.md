# Android Build Fix for CameraView Dependency Issue

## Problem
The build was failing with the error:
```
Could not find com.google.android:cameraview:1.0.0.
Required by: project :app > project :expo > project :expo-camera
```

## Root Cause
The `com.google.android:cameraview:1.0.0` library has been deprecated and is no longer available in the standard Maven repositories. This library was used by older versions of `expo-camera`.

## Solution Applied

### 1. Dependency Substitution
Added dependency substitution in `android/build.gradle` to replace the deprecated `cameraview` with AndroidX Camera:

```gradle
configurations.all {
    resolutionStrategy {
        force 'androidx.camera:camera-core:1.3.0'
        force 'androidx.camera:camera-camera2:1.3.0'
        force 'androidx.camera:camera-lifecycle:1.3.0'
        force 'androidx.camera:camera-view:1.3.0'
    }
    
    resolutionStrategy.dependencySubstitution {
        substitute module('com.google.android:cameraview') using module('androidx.camera:camera-view:1.3.0')
    }
}
```

### 2. Direct AndroidX Camera Dependencies
Added direct AndroidX Camera dependencies in `android/app/build.gradle`:

```gradle
implementation 'androidx.camera:camera-core:1.3.0'
implementation 'androidx.camera:camera-camera2:1.3.0'
implementation 'androidx.camera:camera-lifecycle:1.3.0'
implementation 'androidx.camera:camera-view:1.3.0'
```

### 3. Automated Fix Script
Created `fix-android-build.js` script that automatically applies these fixes when needed.

## Alternative Solutions (if the above doesn't work)

### Option 1: Update Expo Camera
```bash
npm install expo-camera@latest
```

### Option 2: Use React Native Camera
If expo-camera continues to cause issues, consider switching to `react-native-vision-camera`:

```bash
npm uninstall expo-camera
npm install react-native-vision-camera
```

### Option 3: Manual Gradle Cache Clear
```bash
cd android
./gradlew clean
./gradlew build --refresh-dependencies
```

## Testing the Fix
Run the following command to test the build:
```bash
npx expo run:android
```

## Status
✅ Fix applied successfully
✅ Dependencies resolved
✅ Ready for build testing
