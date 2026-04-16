import dotenv from 'dotenv';

dotenv.config();

export const env = {
  PORT: parseInt(process.env.PORT || '4000', 10),
  NODE_ENV: process.env.NODE_ENV || 'development',

  DATABASE_URL: process.env.DATABASE_URL!,

  JWT_SECRET: process.env.JWT_SECRET!,
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',

  MSAL_CLIENT_ID: process.env.MSAL_CLIENT_ID || '',
  MSAL_CLIENT_SECRET: process.env.MSAL_CLIENT_SECRET || '',
  MSAL_TENANT_ID: process.env.MSAL_TENANT_ID || '',
  MSAL_REDIRECT_URI: process.env.MSAL_REDIRECT_URI || 'http://localhost:4000/api/auth/callback',

  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',

  UPLOAD_DIR: process.env.UPLOAD_DIR || './uploads',
  MAX_FILE_SIZE_MB: parseInt(process.env.MAX_FILE_SIZE_MB || '5', 10),
  MAX_FILES_PER_LISTING: parseInt(process.env.MAX_FILES_PER_LISTING || '5', 10),

  CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:3000',
};

// Validate required env vars
const required = ['DATABASE_URL', 'JWT_SECRET'];
for (const key of required) {
  if (!process.env[key]) {
    console.error(`Missing required environment variable: ${key}`);
    process.exit(1);
  }
}
