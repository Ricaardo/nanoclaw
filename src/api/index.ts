import { startApiServer } from './server.js';

console.log('Starting NanoClaw API Server...');

startApiServer().catch((err) => {
  console.error('Failed to start API server:', err);
  process.exit(1);
});
