import { Request, Response, NextFunction } from 'express';
import { checkTexts } from '../services/badWords.service';
import { BAD_WORDS_DETECTED } from '../utils/errors';

export function badWordsFilter(...fields: string[]) {
  return (req: Request, _res: Response, next: NextFunction) => {
    const texts = fields.map((f) => req.body[f]);
    if (checkTexts(...texts)) {
      return next(BAD_WORDS_DETECTED());
    }
    next();
  };
}
