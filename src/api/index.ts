import { startApiServer } from './server.js';
import { initDatabase } from '../db.js';

console.log('Starting NanoClaw API Server...');

// Initialize database
initDatabase();

startApiServer().catch((err) => {
  console.error('Failed to start API server:', err);
  process.exit(1);
});
