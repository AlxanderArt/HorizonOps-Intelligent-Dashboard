/**
 * HorizonOps Frontend Configuration
 * Environment-aware settings for API endpoints
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  apiVersion: 'v1',
};

export const API_BASE = `${config.apiBaseUrl}/api/${config.apiVersion}`;
