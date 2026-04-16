import { Router } from 'express';
import { auth } from '../middleware/auth';
import { admin } from '../middleware/admin';
import * as adminController from '../controllers/admin.controller';

const router = Router();

// All admin routes require auth + admin role
router.use(auth as any, admin as any);

// GET /api/admin/listings — list all listings with optional status filter
router.get('/listings', adminController.getListings as any);

// PATCH /api/admin/listings/:id/approve — approve a listing
router.patch('/listings/:id/approve', adminController.approveListing as any);

// PATCH /api/admin/listings/:id/reject — reject a listing with reason
router.patch('/listings/:id/reject', adminController.rejectListing as any);

// GET /api/admin/stats — dashboard statistics
router.get('/stats', adminController.getStats as any);

export default router;
