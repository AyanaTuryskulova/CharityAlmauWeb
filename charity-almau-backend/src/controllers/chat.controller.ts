import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as chatService from '../services/chat.service';

export async function getChatRooms(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const rooms = await chatService.getChatRooms(req.user!.userId);
    res.json({ success: true, data: rooms });
  } catch (err) {
    next(err);
  }
}

export async function createChatRoom(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const room = await chatService.createOrGetChatRoom(req.body, req.user!.userId);
    res.json({ success: true, data: room });
  } catch (err) {
    next(err);
  }
}

export async function getMessages(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await chatService.getMessages(
      req.params.roomId as string,
      req.query as any,
      req.user!.userId,
    );
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function sendMessage(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const message = await chatService.createMessage(
      req.params.roomId as string,
      req.body.text,
      req.user!.userId,
    );
    res.status(201).json({ success: true, data: message });
  } catch (err) {
    next(err);
  }
}

export async function markAsRead(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await chatService.markAsRead(req.params.roomId as string, req.user!.userId);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}
