# Electronics Store Mobile App

A React Native mobile application for electronics store inventory management with barcode scanning capabilities, built with offline-first architecture and real-time synchronization.

## 🚀 Features

- **Product Management**: View and manage product inventory
- **Barcode Scanning**: Scan product barcodes for quick inventory updates
- **Offline-First**: Full functionality without internet connection with automatic sync
- **Stock Updates**: Real-time stock quantity adjustments with conflict resolution
- **User Authentication**: Secure login system with JWT tokens
- **Cross-Platform**: Works on both Android and iOS with native performance
- **Automated Testing**: Comprehensive test suite with Jest and React Testing Library

## 🛠️ Prerequisites

- Node.js (>= 18.20.8)
- npm (>= 9.x) or yarn (>= 1.22.x)
- Expo CLI (`npm install -g @expo/cli`)
- EAS CLI (`npm install -g eas-cli`)
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

## 🏗️ Architecture

The application follows a modern React Native architecture with the following key components:

1. **State Management**: Redux with Redux Toolkit for global state
2. **Data Layer**: React Query for server state management
3. **Offline Support**: Redux Persist for local data persistence
4. **Navigation**: React Navigation with TypeScript support
5. **UI Components**: React Native Paper for consistent theming and components
6. **Testing**: Jest and React Testing Library for unit and integration tests

### Key Architectural Decisions

- **Offline-First Approach**: All data is stored locally first and synced when online
- **Modular Structure**: Features are organized by domain with clear separation of concerns
- **Type Safety**: TypeScript for better developer experience and code quality
- **Automated Builds**: CI/CD pipeline with EAS for automated builds and deployments

## 🚀 Getting Started

### Environment Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/electronics-store-app.git
   cd electronics-mobile-app
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the environment variables as needed

4. Start the development server:

   ```bash
   npm start
   ```

### Running on Different Platforms

- **Android**: `npm run android`
- **iOS**: `npm run ios` (requires macOS)
- **Web**: `npm run web`

## 🔧 Troubleshooting

### Common Issues

1. **Build Failures**
   - Ensure all dependencies are installed: `npm install`
   - Clear Metro bundler cache: `npm start -- --reset-cache`
   - Check [BUILD_FIXES_SUMMARY.md](./BUILD_FIXES_SUMMARY.md) for known build issues

2. **Android Emulator Not Starting**
   - Make sure Android Studio and Android SDK are properly installed
   - Verify that the emulator is created and working through Android Studio

3. **iOS Build Issues**
   - Run `pod install` in the `ios` directory
   - Ensure Xcode command line tools are installed: `xcode-select --install`

4. **Network Requests Failing**
   - Check if the backend server is running
   - Verify API endpoints in `src/config/api.js`
   - Ensure CORS is properly configured on the backend

### Debugging

- Use React Native Debugger for state inspection
- Enable Remote JS Debugging in the developer menu
- Check Metro bundler logs for runtime errors

## Installation

1. Clone the repository
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   npm install
   ```

## Development

### Start the development server:
```bash
npm start
```

### Run on specific platforms:
```bash
npm run android  # Android
npm run ios      # iOS
npm run web      # Web
```

## Testing

### Run all tests:
```bash
npm test
```

### Run tests in watch mode:
```bash
npm run test:watch
```

### Generate coverage report:
```bash
npm run test:coverage
```

## 🚀 Deployment

### Prerequisites for Building

1. Install EAS CLI: `npm install -g eas-cli`
2. Create an Expo account and login: `eas login`
3. Configure your project: `eas build:configure`

### Android Builds

#### Preview Build (Testing)

```bash
eas build --platform android --profile preview
```

#### Production Build

```bash
eas build --platform android --profile production
```

### iOS Builds

#### Development Build

```bash
eas build --platform ios --profile development
```

#### Production Build (App Store)

```bash
eas build --platform ios --profile production
```

### Environment-Specific Builds

1. **Development**: `eas build --platform all --profile development`
2. **Staging**: `eas build --platform all --profile staging`
3. **Production**: `eas build --platform all --profile production`

## 📚 Documentation

- [Architecture Decision Records (ADR)](./docs/adr/README.md)
- [API Documentation](./docs/API.md)
- [Testing Guide](./docs/TESTING.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Project Structure

```
├── __tests__/          # Test files
├── assets/             # App assets (icons, images)
├── screens/            # Screen components
│   ├── ProductList.js  # Product listing screen
│   ├── ProductDetail.js # Product details screen
│   └── StockUpdate.js  # Stock update screen
├── App.js              # Main app component (navigation)
├── App_Enhanced.js     # Enhanced app with offline support
├── app.json            # Expo configuration
├── eas.json            # EAS Build configuration
└── package.json        # Dependencies and scripts
```

## Configuration

### API Configuration
Update the API base URL in the following files:
- `App_Enhanced.js`: Line 22 (`API_BASE_URL`)
- `screens/ProductList.js`: Line 5 (`API_BASE`)
- `screens/StockUpdate.js`: Line 5 (`API_BASE`)

### App Configuration
Edit `app.json` to customize:
- App name and description
- Bundle identifier
- App icons and splash screen
- Permissions

## Testing Coverage

The app includes comprehensive tests for:
- ✅ Component rendering
- ✅ User interactions
- ✅ API calls and error handling
- ✅ Offline functionality
- ✅ Authentication flow
- ✅ Stock update operations
- ✅ Navigation between screens

## Deployment

### Android APK
1. Run `npm run build:android:production`
2. Download the APK from the Expo build dashboard
3. Install on Android devices or distribute via app stores

### iOS App
1. Run `eas build --platform ios`
2. Submit to App Store or distribute via TestFlight

## Troubleshooting

### Common Issues:

1. **Metro bundler issues**: Clear cache with `npx expo start --clear`
2. **Dependency conflicts**: Delete `node_modules` and run `npm install`
3. **Build failures**: Check EAS build logs for specific errors
4. **Camera permissions**: Ensure camera permissions are granted in device settings

### Debug Mode:
- Enable debug mode in Expo Dev Tools
- Use React Native Debugger for advanced debugging
- Check console logs for error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm test`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review test files for usage examples
- Contact the development team
