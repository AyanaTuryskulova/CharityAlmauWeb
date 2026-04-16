import { Router } from 'express';
import rateLimit from 'express-rate-limit';
import { auth } from '../middleware/auth';
import * as authController from '../controllers/auth.controller';

const router = Router();

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    error: { code: 'AUTH_REQUIRED', message: 'Too many auth attempts, please try again later' },
  },
});

router.get('/login', authLimiter, authController.login);
router.get('/callback', authLimiter, authController.callback);
router.post('/dev-login', authLimiter, authController.devLoginHandler);
router.get('/me', auth, authController.me);

export default router;
