#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

console.log('🧪 Running Electronics Store Mobile App Tests...\n');

try {
  // Check if node_modules exists
  const fs = require('fs');
  if (!fs.existsSync('./node_modules')) {
    console.log('📦 Installing dependencies...');
    execSync('npm install', { stdio: 'inherit' });
  }

  // Run tests
  console.log('🔍 Running Jest tests...');
  execSync('npx jest --verbose --coverage', { stdio: 'inherit' });

  console.log('\n✅ All tests completed successfully!');
} catch (error) {
  console.error('\n❌ Tests failed:', error.message);
  process.exit(1);
}
