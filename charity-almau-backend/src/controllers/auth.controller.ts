import { Request, Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import { env } from '../config/env';
import * as authService from '../services/auth.service';
import { VALIDATION_ERROR, USER_NOT_FOUND } from '../utils/errors';

export async function login(_req: Request, res: Response) {
  const url = authService.getLoginUrl();
  res.redirect(url);
}

export async function callback(req: Request, res: Response, next: NextFunction) {
  try {
    const code = req.query.code as string;
    if (!code) {
      throw VALIDATION_ERROR('Authorization code is required');
    }

    const { token, user } = await authService.handleCallback(code);

    // Redirect to frontend with token
    res.redirect(`${env.CORS_ORIGIN}/auth/callback?token=${token}`);
  } catch (err) {
    next(err);
  }
}

export async function devLoginHandler(req: Request, res: Response, next: NextFunction) {
  try {
    if (env.NODE_ENV !== 'development') {
      throw VALIDATION_ERROR('Dev login is only available in development mode');
    }

    const { email, name } = req.body;
    if (!email || !name) {
      throw VALIDATION_ERROR('Email and name are required');
    }

    const { token, user } = await authService.devLogin(email, name);

    res.json({ success: true, data: { token, user } });
  } catch (err) {
    next(err);
  }
}

export async function me(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const user = await authService.getMe(req.user!.userId);
    if (!user) {
      throw USER_NOT_FOUND();
    }

    res.json({ success: true, data: { user } });
  } catch (err) {
    next(err);
  }
}
