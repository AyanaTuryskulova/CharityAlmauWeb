import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as adminService from '../services/admin.service';
import { VALIDATION_ERROR } from '../utils/errors';

export async function getListings(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const result = await adminService.getListings(req.query as any);
    res.json({ success: true, data: result.data, meta: result.meta });
  } catch (err) {
    next(err);
  }
}

export async function approveListing(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    const listing = await adminService.approveListing(id);
    res.json({ success: true, data: listing });
  } catch (err) {
    next(err);
  }
}

export async function rejectListing(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const id = req.params.id as string;
    const { reason } = req.body;
    if (!reason || typeof reason !== 'string' || reason.trim().length === 0) {
      throw VALIDATION_ERROR('Reject reason is required');
    }
    const listing = await adminService.rejectListing(id, reason.trim());
    res.json({ success: true, data: listing });
  } catch (err) {
    next(err);
  }
}

export async function getStats(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const stats = await adminService.getStats();
    res.json({ success: true, data: stats });
  } catch (err) {
    next(err);
  }
}
