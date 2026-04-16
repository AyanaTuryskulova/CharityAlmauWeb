import multer from 'multer';
import { Request } from 'express';
import { env } from '../config/env';
import { UPLOAD_INVALID_TYPE } from '../utils/errors';

const ALLOWED_MIMES = ['image/jpeg', 'image/png', 'image/webp'];

const storage = multer.memoryStorage();

const fileFilter = (_req: Request, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
  if (ALLOWED_MIMES.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(UPLOAD_INVALID_TYPE());
  }
};

const limits = {
  fileSize: env.MAX_FILE_SIZE_MB * 1024 * 1024,
};

// For listing images — up to MAX_FILES_PER_LISTING files
export const uploadListingImages = multer({ storage, fileFilter, limits }).array(
  'images',
  env.MAX_FILES_PER_LISTING
);

// For single avatar
export const uploadAvatar = multer({ storage, fileFilter, limits }).single('avatar');

// For single AI image analysis
export const uploadSingleImage = multer({ storage, fileFilter, limits }).single('image');
