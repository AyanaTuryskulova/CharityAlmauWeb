import { Response, NextFunction } from 'express';
import { AuthRequest } from '../types';
import * as aiService from '../services/ai.service';
import { AI_INVALID_IMAGE } from '../utils/errors';

export async function analyzeImage(req: AuthRequest, res: Response, next: NextFunction) {
  try {
    const file = req.file;
    if (!file) {
      throw AI_INVALID_IMAGE('No image provided');
    }

    const result = await aiService.analyzeImage(file.buffer, file.mimetype);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}
