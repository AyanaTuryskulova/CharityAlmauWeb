import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as listingsService from '../services/listings.service';

export async function getListings(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await listingsService.getListings(req.query as any, req.user?.userId);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function getListingById(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    const listing = await listingsService.getListingById(id, req.user?.userId);
    res.json({ success: true, data: listing });
  } catch (err) {
    next(err);
  }
}

export async function createListing(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const files = (req.files as Express.Multer.File[]) || [];
    const listing = await listingsService.createListing(req.body, files, req.user!.userId);
    res.status(201).json({ success: true, data: listing });
  } catch (err) {
    next(err);
  }
}

export async function updateListing(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    const files = (req.files as Express.Multer.File[]) || [];
    const listing = await listingsService.updateListing(
      id,
      req.body,
      files,
      req.user!.userId
    );
    res.json({ success: true, data: listing });
  } catch (err) {
    next(err);
  }
}

export async function deleteListing(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    await listingsService.deleteListing(id, req.user!.userId, req.user!.role);
    res.json({ success: true, data: null });
  } catch (err) {
    next(err);
  }
}

export async function getSimilarListings(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    const listings = await listingsService.getSimilarListings(id, req.user?.userId);
    res.json({ success: true, data: listings });
  } catch (err) {
    next(err);
  }
}
