import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import { ADMIN_REQUIRED } from '../utils/errors';

export function admin(req: AuthRequest, _res: Response, next: NextFunction) {
  if (!req.user || req.user.role !== 'ADMIN') {
    return next(ADMIN_REQUIRED());
  }
  next();
}
