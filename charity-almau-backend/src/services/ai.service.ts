import OpenAI from 'openai';
import { env } from '../config/env';
import { AI_SERVICE_UNAVAILABLE, AI_INVALID_IMAGE } from '../utils/errors';

const VALID_CATEGORIES = [
  'TEXTBOOKS',
  'TECH',
  'FURNITURE',
  'CLOTHING',
  'SPORTS',
  'STATIONERY',
  'OTHER',
] as const;

type Category = (typeof VALID_CATEGORIES)[number];

interface AnalysisResult {
  suggestedTitle: string;
  suggestedCategory: Category;
  confidence: number;
}

export async function analyzeImage(buffer: Buffer, mimetype: string): Promise<AnalysisResult> {
  if (!env.OPENAI_API_KEY) {
    return { suggestedTitle: '', suggestedCategory: 'OTHER', confidence: 0 };
  }

  const openai = new OpenAI({ apiKey: env.OPENAI_API_KEY });

  const base64 = buffer.toString('base64');
  const dataUrl = `data:${mimetype};base64,${base64}`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content:
            'You analyze photos of items that students want to give away, exchange, or rent. ' +
            'Return ONLY valid JSON (no markdown, no code fences): ' +
            '{ "title": string (short title in Russian, max 100 chars), ' +
            '"category": "TEXTBOOKS" | "TECH" | "FURNITURE" | "CLOTHING" | "SPORTS" | "STATIONERY" | "OTHER", ' +
            '"confidence": number (0 to 1, how confident you are) }',
        },
        {
          role: 'user',
          content: [
            { type: 'text', text: 'What is this item? Suggest a title and category.' },
            { type: 'image_url', image_url: { url: dataUrl, detail: 'low' } },
          ],
        },
      ],
      max_tokens: 200,
      temperature: 0.3,
    });

    const text = response.choices[0]?.message?.content?.trim();
    if (!text) {
      return { suggestedTitle: '', suggestedCategory: 'OTHER', confidence: 0 };
    }

    const parsed = JSON.parse(text);

    const suggestedTitle =
      typeof parsed.title === 'string' ? parsed.title.slice(0, 200) : '';
    const suggestedCategory = VALID_CATEGORIES.includes(parsed.category)
      ? (parsed.category as Category)
      : 'OTHER';
    const confidence =
      typeof parsed.confidence === 'number'
        ? Math.max(0, Math.min(1, parsed.confidence))
        : 0;

    return { suggestedTitle, suggestedCategory, confidence };
  } catch (err: any) {
    if (err?.status === 400) {
      throw AI_INVALID_IMAGE();
    }
    throw AI_SERVICE_UNAVAILABLE();
  }
}
