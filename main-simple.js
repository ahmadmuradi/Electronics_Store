// Simple Electron main process test
console.log('Starting Electron app...');

const electron = require('electron');
console.log('Electron loaded:', typeof electron);

const app = electron.app;
const BrowserWindow = electron.BrowserWindow;

console.log('App:', typeof app);
console.log('BrowserWindow:', typeof BrowserWindow);

if (!app) {
  console.error('App is undefined!');
  process.exit(1);
}

let mainWindow;

function createWindow() {
  console.log('Creating window...');
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile('index.html');
  console.log('Window created successfully');
}

console.log('Setting up app ready handler...');
app.whenReady().then(() => {
  console.log('App is ready!');
  createWindow();
});

app.on('window-all-closed', () => {
  console.log('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

console.log('Main process setup complete');
