import { Router } from 'express';
import { auth, optionalAuth } from '../middleware/auth';
import { uploadListingImages } from '../middleware/upload';
import { badWordsFilter } from '../middleware/badWords';
import * as listingsController from '../controllers/listings.controller';

const router = Router();

// GET /api/listings — list with filters + pagination
router.get('/', optionalAuth as any, listingsController.getListings as any);

// GET /api/listings/:id — single listing
router.get('/:id', optionalAuth as any, listingsController.getListingById as any);

// GET /api/listings/:id/similar — similar listings
router.get('/:id/similar', optionalAuth as any, listingsController.getSimilarListings as any);

// POST /api/listings — create listing (multipart)
router.post(
  '/',
  auth as any,
  uploadListingImages,
  badWordsFilter('title', 'description') as any,
  listingsController.createListing as any
);

// PUT /api/listings/:id — update listing (multipart)
router.put(
  '/:id',
  auth as any,
  uploadListingImages,
  badWordsFilter('title', 'description') as any,
  listingsController.updateListing as any
);

// DELETE /api/listings/:id — delete listing
router.delete('/:id', auth as any, listingsController.deleteListing as any);

export default router;
