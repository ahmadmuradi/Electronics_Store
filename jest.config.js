module.exports = {
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  testMatch: [
    '<rootDir>/tests/**/*.test.js',
    '<rootDir>/tests/**/*.spec.js'
  ],
  collectCoverageFrom: [
    '*.js',
    '!main.js', // Exclude main process from coverage as it requires Electron
    '!jest.config.js',
    '!build-simple.js',
    '!create-installer.ps1'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  testTimeout: 30000,
  verbose: true,
  moduleFileExtensions: ['js', 'json'],
  transform: {},
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
    '/releases/'
  ]
};
