import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as favoritesService from '../services/favorites.service';

export async function addFavorite(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const { listingId } = req.body;
    const favorite = await favoritesService.addFavorite(listingId, req.user!.userId);
    res.status(201).json({ success: true, data: favorite });
  } catch (err) {
    next(err);
  }
}

export async function removeFavorite(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const listingId = req.params.listingId as string;
    await favoritesService.removeFavorite(listingId, req.user!.userId);
    res.json({ success: true, data: null });
  } catch (err) {
    next(err);
  }
}

export async function getFavorites(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await favoritesService.getFavorites(req.query as any, req.user!.userId);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}
