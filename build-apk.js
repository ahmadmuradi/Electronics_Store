#!/usr/bin/env node

/**
 * Enhanced APK Build Script for Electronics Store Mobile App
 * Automates the APK creation process with multiple build options
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Build configurations
const BUILD_PROFILES = {
  debug: {
    profile: 'development',
    description: 'Debug APK with development features',
    time: '8-12 minutes',
  },
  preview: {
    profile: 'preview',
    description: 'Preview APK for testing',
    time: '10-15 minutes',
  },
  production: {
    profile: 'production-apk',
    description: 'Production APK optimized for distribution',
    time: '12-18 minutes',
  },
};

class APKBuilder {
  constructor() {
    this.startTime = Date.now();
    this.buildType = process.argv[2] || 'preview';
  }

  log(message, color = 'reset') {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`${colors[color]}[${timestamp}] ${message}${colors.reset}`);
  }

  error(message) {
    this.log(`❌ ERROR: ${message}`, 'red');
  }

  success(message) {
    this.log(`✅ SUCCESS: ${message}`, 'green');
  }

  info(message) {
    this.log(`ℹ️  INFO: ${message}`, 'blue');
  }

  warning(message) {
    this.log(`⚠️  WARNING: ${message}`, 'yellow');
  }

  async executeCommand(command, description) {
    this.info(`${description}...`);
    try {
      const output = execSync(command, {
        stdio: 'pipe',
        encoding: 'utf8',
        maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      });
      this.success(`${description} completed`);
      return output;
    } catch (error) {
      this.error(`${description} failed: ${error.message}`);
      throw error;
    }
  }

  checkPrerequisites() {
    this.info('Checking prerequisites...');

    // Check if EAS CLI is installed
    try {
      execSync('eas --version', { stdio: 'pipe' });
      this.success('EAS CLI is installed');
    } catch (error) {
      this.error('EAS CLI not found. Install with: npm install -g eas-cli');
      process.exit(1);
    }

    // Check if user is logged in
    try {
      const whoami = execSync('eas whoami', { stdio: 'pipe', encoding: 'utf8' });
      this.success(`Logged in as: ${whoami.trim()}`);
    } catch (error) {
      this.error('Not logged in to Expo. Run: eas login');
      process.exit(1);
    }

    // Check if project is configured
    if (!fs.existsSync('eas.json')) {
      this.error('eas.json not found. Run: eas build:configure');
      process.exit(1);
    }

    this.success('All prerequisites met');
  }

  validateBuildType() {
    if (!BUILD_PROFILES[this.buildType]) {
      this.error(`Invalid build type: ${this.buildType}`);
      this.info('Available build types:');
      Object.keys(BUILD_PROFILES).forEach(type => {
        const config = BUILD_PROFILES[type];
        console.log(
          `  ${colors.cyan}${type}${colors.reset}: ${config.description} (${config.time})`
        );
      });
      process.exit(1);
    }
  }

  displayBuildInfo() {
    const config = BUILD_PROFILES[this.buildType];
    console.log(`\n${colors.bright}🚀 Electronics Store Mobile App - APK Builder${colors.reset}`);
    console.log(`${colors.bright}================================================${colors.reset}`);
    console.log(`Build Type: ${colors.cyan}${this.buildType}${colors.reset}`);
    console.log(`Profile: ${colors.cyan}${config.profile}${colors.reset}`);
    console.log(`Description: ${config.description}`);
    console.log(`Estimated Time: ${config.time}`);
    console.log(
      `${colors.bright}================================================${colors.reset}\n`
    );
  }

  async cleanEnvironment() {
    this.info('Cleaning build environment...');

    try {
      // Clear Expo cache
      await this.executeCommand('npx expo start --clear --non-interactive', 'Clearing Expo cache');

      // Clear npm cache
      await this.executeCommand('npm cache clean --force', 'Clearing npm cache');

      this.success('Environment cleaned');
    } catch (error) {
      this.warning('Some cleanup operations failed, continuing...');
    }
  }

  async validateConfiguration() {
    this.info('Validating project configuration...');

    try {
      // Validate Expo configuration
      await this.executeCommand('npx expo config --type public', 'Validating Expo config');

      // Check dependencies
      await this.executeCommand('npm ls --depth=0', 'Checking dependencies');

      this.success('Configuration validated');
    } catch (error) {
      this.warning('Configuration validation had issues, but continuing...');
    }
  }

  async buildAPK() {
    const config = BUILD_PROFILES[this.buildType];
    const buildCommand = `eas build --platform android --profile ${config.profile} --non-interactive`;

    this.info(`Starting ${this.buildType} build...`);
    this.info(`Command: ${buildCommand}`);

    try {
      const output = await this.executeCommand(buildCommand, `Building ${this.buildType} APK`);

      // Extract build URL from output
      const urlMatch = output.match(/https:\/\/expo\.dev\/accounts\/[^\s]+/);
      if (urlMatch) {
        this.success(`Build started successfully!`);
        this.info(`Build URL: ${colors.cyan}${urlMatch[0]}${colors.reset}`);
        this.info(`You can monitor the build progress at the URL above`);
      }

      return output;
    } catch (error) {
      this.error('Build failed. Check the error message above.');
      throw error;
    }
  }

  async monitorBuild() {
    this.info('You can monitor your build with these commands:');
    console.log(`  ${colors.cyan}npm run build:status${colors.reset} - List all builds`);
    console.log(`  ${colors.cyan}eas build:list${colors.reset} - View build history`);
    console.log(
      `  ${colors.cyan}eas build:view [BUILD_ID]${colors.reset} - View specific build details`
    );
  }

  displayCompletionInfo() {
    const elapsedTime = Math.round((Date.now() - this.startTime) / 1000);

    console.log(`\n${colors.bright}🎉 Build Process Completed!${colors.reset}`);
    console.log(`${colors.bright}================================${colors.reset}`);
    console.log(`Build Type: ${colors.cyan}${this.buildType}${colors.reset}`);
    console.log(`Time Elapsed: ${colors.cyan}${elapsedTime} seconds${colors.reset}`);
    console.log(`\n${colors.bright}Next Steps:${colors.reset}`);
    console.log(`1. Monitor build progress at expo.dev`);
    console.log(`2. Download APK when build completes`);
    console.log(`3. Install on Android device for testing`);
    console.log(`4. Test all app functionality`);
    console.log(`\n${colors.bright}Useful Commands:${colors.reset}`);
    console.log(`${colors.cyan}npm run build:status${colors.reset} - Check build status`);
    console.log(`${colors.cyan}npm run build:cancel${colors.reset} - Cancel current build`);
    console.log(
      `${colors.cyan}node build-apk.js [debug|preview|production]${colors.reset} - Build different APK types`
    );
  }

  async run() {
    try {
      console.clear();
      this.displayBuildInfo();
      this.validateBuildType();
      this.checkPrerequisites();
      await this.cleanEnvironment();
      await this.validateConfiguration();
      await this.buildAPK();
      await this.monitorBuild();
      this.displayCompletionInfo();
    } catch (error) {
      this.error(`Build process failed: ${error.message}`);
      console.log(`\n${colors.bright}Troubleshooting Tips:${colors.reset}`);
      console.log(`1. Check your internet connection`);
      console.log(`2. Verify EAS CLI is up to date: npm install -g eas-cli@latest`);
      console.log(`3. Ensure you're logged in: eas login`);
      console.log(`4. Check build logs: eas build:list`);
      console.log(`5. Try cleaning environment: npm run clean:cache`);
      process.exit(1);
    }
  }
}

// Display usage information
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
${colors.bright}Electronics Store Mobile App - APK Builder${colors.reset}

${colors.bright}Usage:${colors.reset}
  node build-apk.js [build-type]

${colors.bright}Build Types:${colors.reset}
  debug      - Debug APK with development features (8-12 minutes)
  preview    - Preview APK for testing (10-15 minutes) [default]
  production - Production APK optimized for distribution (12-18 minutes)

${colors.bright}Examples:${colors.reset}
  node build-apk.js preview     # Build preview APK
  node build-apk.js production  # Build production APK
  node build-apk.js debug       # Build debug APK

${colors.bright}Prerequisites:${colors.reset}
  - EAS CLI installed: npm install -g eas-cli
  - Logged in to Expo: eas login
  - Project configured: eas build:configure

${colors.bright}Monitoring:${colors.reset}
  npm run build:status  # Check build status
  npm run build:cancel  # Cancel current build
`);
  process.exit(0);
}

// Run the builder
const builder = new APKBuilder();
builder.run();
