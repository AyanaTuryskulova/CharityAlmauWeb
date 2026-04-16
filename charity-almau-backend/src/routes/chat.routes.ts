import { Router } from 'express';
import { auth } from '../middleware/auth';
import { validate } from '../middleware/validate';
import { z } from 'zod';
import * as chatController from '../controllers/chat.controller';

const router = Router();

const createRoomSchema = z.object({
  otherUserId: z.string().uuid(),
  listingId: z.string().uuid().optional(),
});

// GET /api/chat/rooms — get all chat rooms
router.get('/rooms', auth as any, chatController.getChatRooms as any);

// POST /api/chat/rooms — create or get chat room
router.post(
  '/rooms',
  auth as any,
  validate(createRoomSchema) as any,
  chatController.createChatRoom as any,
);

// GET /api/chat/rooms/:roomId/messages — get messages
router.get('/rooms/:roomId/messages', auth as any, chatController.getMessages as any);

// POST /api/chat/rooms/:roomId/messages — send message
router.post(
  '/rooms/:roomId/messages',
  auth as any,
  validate(z.object({ text: z.string().min(1).max(2000) })) as any,
  chatController.sendMessage as any,
);

// POST /api/chat/rooms/:roomId/read — mark as read
router.post('/rooms/:roomId/read', auth as any, chatController.markAsRead as any);

export default router;
