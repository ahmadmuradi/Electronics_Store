import Constants from 'expo-constants';
import { Platform } from 'react-native';
import * as Sentry from 'sentry-expo';

// Initialize Sentry
const initSentry = () => {
  if (!Constants.expoConfig?.extra?.sentryDsn) {
    console.warn('Sentry DSN not configured. Error tracking will be disabled.');
    return;
  }

  Sentry.init({
    dsn: Constants.expoConfig.extra.sentryDsn,
    enableInExpoDevelopment: false, // Set to true in development if needed
    debug: __DEV__,
    environment: Constants.expoConfig.extra?.env || 'development',
    release: `${Constants.expoConfig.slug}@${Constants.expoConfig.version}`,
    dist: Constants.expoConfig.version,
    // Filter out common false positives
    beforeSend(event, hint) {
      const error = hint?.originalException;

      // Ignore specific errors
      if (
        error?.message?.includes('Network request failed') ||
        error?.message?.includes('Failed to fetch')
      ) {
        return null;
      }

      // Add device info to all events
      event.tags = {
        ...event.tags,
        platform: Platform.OS,
        deviceId: Constants.deviceId,
      };

      return event;
    },
  });

  // Set user context when available
  const setUserContext = user => {
    if (user) {
      Sentry.Native.setUser({
        id: user.id,
        email: user.email,
        username: user.username,
      });
    } else {
      Sentry.Native.setUser(null);
    }
  };

  return {
    setUserContext,
  };
};

export const sentry = initSentry();

// Error boundary component for React
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    Sentry.Native.captureException(error, {
      tags: { type: 'react_boundary' },
      extra: errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return this.props.fallback || <Text>Something went wrong.</Text>;
    }

    return this.props.children;
  }
}

export { ErrorBoundary };

// Helper function to capture exceptions
export const captureException = (error, context = {}) => {
  console.error('Captured exception:', error, context);

  if (__DEV__) {
    // Don't send to Sentry in development
    return;
  }

  Sentry.Native.captureException(error, {
    extra: context,
  });
};

// Helper function to capture messages
export const captureMessage = (message, level = 'info', context = {}) => {
  console[level](`[${level.toUpperCase()}]`, message, context);

  if (__DEV__) {
    // Don't send to Sentry in development
    return;
  }

  Sentry.Native.captureMessage(message, {
    level,
    extra: context,
  });
};
