#!/usr/bin/env node
// save this as build-apk-enhanced.js
const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class EnhancedAPKBuilder {
  constructor() {
    this.colors = {
      reset: '\x1b[0m',
      red: '\x1b[31m',
      green: '\x1b[32m',
      yellow: '\x1b[33m',
      blue: '\x1b[34m',
    };
  }

  log(message, color = 'reset') {
    console.log(`${this.colors[color]}${message}${this.colors.reset}`);
  }

  async runCommand(command, description, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        this.log(`🔄 ${description}...`, 'blue');
        execSync(command, { stdio: 'inherit', timeout: 300000 });
        this.log(`✅ ${description} completed`, 'green');
        return true;
      } catch (error) {
        this.log(`❌ Attempt ${i + 1} failed: ${error.message}`, 'yellow');
        if (i === retries - 1) return false;
      }
    }
  }

  verifyDependencies() {
    this.log('🔍 Verifying critical dependencies...', 'yellow');

    const criticalPackages = [
      'expo',
      'react-native',
      'es-abstract',
      '@react-native-async-storage/async-storage',
    ];

    let allGood = true;
    criticalPackages.forEach(pkg => {
      try {
        require.resolve(pkg);
        this.log(`✅ ${pkg} - OK`, 'green');
      } catch (error) {
        this.log(`❌ ${pkg} - MISSING`, 'red');
        allGood = false;
      }
    });

    return allGood;
  }

  async fixESAbstract() {
    this.log('🔧 Fixing es-abstract issues...', 'yellow');

    // Create a temporary fix for es-abstract
    const esAbstractFix = `
// Temporary fix for es-abstract bytesAsFloat32
module.exports = function bytesAsFloat32(bytes, littleEndian = false) {
  const buffer = new ArrayBuffer(4);
  const view = new DataView(buffer);
  bytes.forEach((byte, index) => {
    view.setUint8(index, byte);
  });
  return view.getFloat32(0, littleEndian);
};
`;

    const helpersDir = path.join('node_modules', 'es-abstract', 'helpers');
    if (!fs.existsSync(helpersDir)) {
      fs.mkdirSync(helpersDir, { recursive: true });
    }

    fs.writeFileSync(path.join(helpersDir, 'bytesAsFloat32.js'), esAbstractFix);
    this.log('✅ Applied es-abstract temporary fix', 'green');
  }

  async build() {
    this.log('🚀 Starting Enhanced APK Build Process', 'blue');

    // Step 1: Clean and verify
    await this.runCommand('npm run clean', 'Clean project');

    // Step 2: Install dependencies
    if (!(await this.runCommand('npm install --legacy-peer-deps', 'Install dependencies', 3))) {
      this.log('⚠️  Using fallback installation method...', 'yellow');
      await this.runCommand('npm install --production --no-optional', 'Minimal installation');
    }

    // Step 3: Apply es-abstract fix
    await this.fixESAbstract();

    // Step 4: Verify dependencies
    if (!this.verifyDependencies()) {
      this.log('❌ Critical dependencies missing, cannot proceed', 'red');
      process.exit(1);
    }

    // Step 5: Prebuild
    await this.runCommand('npx expo prebuild --clean', 'Generate native projects');

    // Step 6: Build APK
    if (
      await this.runCommand(
        'eas build --platform android --profile preview --non-interactive',
        'Build APK'
      )
    ) {
      this.log('🎉 APK build completed successfully!', 'green');
    } else {
      this.log('❌ APK build failed', 'red');
    }
  }
}

new EnhancedAPKBuilder().build();
