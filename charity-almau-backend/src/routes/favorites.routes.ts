import { Router } from 'express';
import { auth } from '../middleware/auth';
import * as favoritesController from '../controllers/favorites.controller';

const router = Router();

// POST /api/favorites — add to favorites
router.post('/', auth as any, favoritesController.addFavorite as any);

// DELETE /api/favorites/:listingId — remove from favorites
router.delete('/:listingId', auth as any, favoritesController.removeFavorite as any);

// GET /api/favorites — list user's favorites
router.get('/', auth as any, favoritesController.getFavorites as any);

export default router;
