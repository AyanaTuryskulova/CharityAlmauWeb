import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as usersService from '../services/users.service';

export async function getUserById(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const user = await usersService.getUserById(req.params.id as string);
    res.json({ success: true, data: user });
  } catch (err) {
    next(err);
  }
}

export async function updateProfile(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const user = await usersService.updateProfile(
      req.user!.userId,
      req.body,
      req.file as Express.Multer.File | undefined,
    );
    res.json({ success: true, data: user });
  } catch (err) {
    next(err);
  }
}

export async function getUserRatings(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await usersService.getUserRatings(req.params.id as string, req.query as any);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function createRating(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const rating = await usersService.createRating(req.params.id as string, req.user!.userId, req.body);
    res.status(201).json({ success: true, data: rating });
  } catch (err) {
    next(err);
  }
}
