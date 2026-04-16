import { Router } from 'express';
import { auth } from '../middleware/auth';
import { validate } from '../middleware/validate';
import { badWordsFilter } from '../middleware/badWords';
import { z } from 'zod';
import * as requestsController from '../controllers/requests.controller';

const router = Router();

const createRequestSchema = z.object({
  listingId: z.string().uuid(),
  message: z.string().max(1000).optional(),
});

// POST /api/requests — create request
router.post(
  '/',
  auth as any,
  validate(createRequestSchema) as any,
  badWordsFilter('message') as any,
  requestsController.createRequest as any,
);

// GET /api/requests/incoming — get incoming requests
router.get('/incoming', auth as any, requestsController.getIncomingRequests as any);

// GET /api/requests/outgoing — get outgoing requests
router.get('/outgoing', auth as any, requestsController.getOutgoingRequests as any);

// PATCH /api/requests/:id/accept
router.patch('/:id/accept', auth as any, requestsController.acceptRequest as any);

// PATCH /api/requests/:id/reject
router.patch('/:id/reject', auth as any, requestsController.rejectRequest as any);

// PATCH /api/requests/:id/cancel
router.patch('/:id/cancel', auth as any, requestsController.cancelRequest as any);

export default router;
