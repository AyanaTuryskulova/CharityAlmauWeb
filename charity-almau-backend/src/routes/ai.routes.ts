import { Router } from 'express';
import multer from 'multer';
import { auth } from '../middleware/auth';
import * as aiController from '../controllers/ai.controller';
import { env } from '../config/env';
import { UPLOAD_INVALID_TYPE } from '../utils/errors';

const ALLOWED_MIMES = ['image/jpeg', 'image/png', 'image/webp'];

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: env.MAX_FILE_SIZE_MB * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (ALLOWED_MIMES.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(UPLOAD_INVALID_TYPE());
    }
  },
}).single('image');

const router = Router();

// POST /api/ai/analyze-image — analyze image with AI
router.post('/analyze-image', auth as any, upload, aiController.analyzeImage as any);

export default router;
