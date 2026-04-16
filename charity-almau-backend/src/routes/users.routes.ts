import { Router } from 'express';
import { auth, optionalAuth } from '../middleware/auth';
import { validate } from '../middleware/validate';
import { badWordsFilter } from '../middleware/badWords';
import { uploadAvatar } from '../middleware/upload';
import { z } from 'zod';
import * as usersController from '../controllers/users.controller';

const router = Router();

const createRatingSchema = z.object({
  score: z.number().int().min(1).max(5),
  comment: z.string().max(1000).optional(),
  listingId: z.string().uuid().optional(),
});

// PUT /api/users/me — update own profile
router.put(
  '/me',
  auth as any,
  uploadAvatar as any,
  usersController.updateProfile as any,
);

// GET /api/users/:id — get user profile
router.get('/:id', optionalAuth as any, usersController.getUserById as any);

// GET /api/users/:id/ratings — get user ratings
router.get('/:id/ratings', optionalAuth as any, usersController.getUserRatings as any);

// POST /api/users/:id/ratings — create rating
router.post(
  '/:id/ratings',
  auth as any,
  validate(createRatingSchema) as any,
  badWordsFilter('comment') as any,
  usersController.createRating as any,
);

export default router;
