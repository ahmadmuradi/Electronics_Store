# 📱 APK Quick Reference - Electronics Store Mobile App

## 🚀 Quick Commands

### Instant Testing (2 minutes)
```bash
npm start                    # Start Expo Go development server
# Scan QR code with Expo Go app on your phone
```

### Build APK (10-15 minutes)
```bash
npm run build:android       # Preview APK for testing
npm run build:android:production-apk  # Production APK
```

### Automated Build Script
```bash
node build-apk.js preview    # Automated preview build
node build-apk.js production # Automated production build
node build-apk.js debug      # Automated debug build
```

### Monitor Builds
```bash
npm run build:status        # Check build status
eas build:list              # View build history
eas build:view [BUILD_ID]   # View specific build
```

## 🎯 Build Types Comparison

| Type | Profile | Use Case | Time | Size |
|------|---------|----------|------|------|
| **Debug** | development | Development & debugging | 8-12 min | ~30MB |
| **Preview** | preview | Testing & QA | 10-15 min | ~25MB |
| **Production** | production-apk | Distribution | 12-18 min | ~20MB |

## 📋 Prerequisites Checklist

- [ ] **EAS CLI installed**: `npm install -g eas-cli`
- [ ] **Logged in to Expo**: `eas login`
- [ ] **Project configured**: `eas build:configure` (already done)
- [ ] **Dependencies updated**: `npm install`

## 🔧 Troubleshooting Quick Fixes

### Build Fails
```bash
npm run clean:cache         # Clear all caches
npm run validate            # Check configuration
eas build:list              # Check previous builds
```

### Keystore Issues
```bash
eas credentials             # Manage keystores
# Follow prompts to create/upload keystore
```

### Memory/Timeout Issues
```bash
eas build --platform android --profile preview --clear-cache
```

## 📱 Device Installation

### Android Device Setup
1. **Enable Developer Options**: Settings → About → Tap "Build number" 7 times
2. **Enable Unknown Sources**: Settings → Security → Unknown sources
3. **Install APK**: Transfer file and tap to install
4. **Grant Permissions**: Allow camera access for barcode scanning

### Testing Checklist
- [ ] App launches successfully
- [ ] Login works
- [ ] Product list loads
- [ ] Barcode scanner opens
- [ ] Stock updates save
- [ ] Offline mode works
- [ ] Navigation functions

## 🌐 Alternative Methods

### Expo Go (Instant)
```bash
npm start
# Scan QR code with Expo Go app
```

### Web Version
```bash
npm run web
# Test in browser at localhost:19006
```

### Local Build (Advanced)
```bash
npx expo run:android --variant release
# Requires Android Studio setup
```

## 📊 Build Status Codes

- **🟢 FINISHED**: Build completed successfully
- **🟡 IN_PROGRESS**: Build is currently running
- **🔴 ERRORED**: Build failed (check logs)
- **⚪ PENDING**: Build queued, waiting to start
- **🟠 CANCELED**: Build was manually canceled

## 🎉 Success Indicators

### Build Success
- ✅ No error messages in build logs
- ✅ APK download link provided
- ✅ File size between 15-30MB
- ✅ Build status shows "FINISHED"

### App Success
- ✅ Installs without errors
- ✅ All screens load properly
- ✅ Camera permissions work
- ✅ Data persists offline
- ✅ Performance is smooth

## 📞 Quick Help

### Common Commands
```bash
# Build commands
npm run build:android                    # Preview build
npm run build:android:production-apk    # Production build
npm run build:android:debug             # Debug build

# Monitoring
npm run build:status                     # Check status
npm run build:cancel                     # Cancel build

# Maintenance
npm run clean                           # Clean dependencies
npm run clean:cache                     # Clear caches
npm run validate                        # Validate config

# Automated
node build-apk.js [type]                # Automated build
node build-apk.js --help                # Show help
```

### Build URLs
- **Expo Dashboard**: https://expo.dev
- **Build Logs**: Available in dashboard
- **Download Links**: Provided after successful build

## 🚨 Emergency Procedures

### If Build Keeps Failing
1. Clear all caches: `npm run clean:cache`
2. Reinstall dependencies: `npm run clean`
3. Check EAS status: https://status.expo.dev
4. Try different build profile
5. Contact support with build ID

### If APK Won't Install
1. Check Android version (minimum API 21)
2. Enable "Unknown Sources"
3. Clear device storage space
4. Try different APK build type
5. Check device compatibility

---

**📱 Your Electronics Store Mobile App is ready for deployment!**

*For detailed instructions, see `ENHANCED_APK_CREATION_GUIDE.md`*
