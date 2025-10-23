try {
  const electron = require('electron');
  console.log('Electron type:', typeof electron);
  console.log('Electron keys:', Object.keys(electron));
  console.log('App exists:', !!electron.app);
} catch (error) {
  console.error('Error requiring electron:', error);
}