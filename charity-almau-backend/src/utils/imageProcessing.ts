import sharp from 'sharp';
import path from 'path';
import fs from 'fs';
import { v4 as uuidv4 } from 'uuid';
import { env } from '../config/env';

// Ensure uploads directory exists
const uploadsDir = path.resolve(env.UPLOAD_DIR);
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

export async function processListingImage(buffer: Buffer): Promise<string> {
  const filename = `${uuidv4()}.webp`;
  const filepath = path.join(uploadsDir, filename);

  await sharp(buffer)
    .resize({ width: 1200, withoutEnlargement: true })
    .webp({ quality: 80 })
    .toFile(filepath);

  return `/uploads/${filename}`;
}

export async function processAvatarImage(buffer: Buffer): Promise<string> {
  const filename = `${uuidv4()}.webp`;
  const filepath = path.join(uploadsDir, filename);

  await sharp(buffer)
    .resize(400, 400, { fit: 'cover' })
    .webp({ quality: 80 })
    .toFile(filepath);

  return `/uploads/${filename}`;
}

export function deleteImage(imagePath: string): void {
  const filename = path.basename(imagePath);
  const filepath = path.join(uploadsDir, filename);
  if (fs.existsSync(filepath)) {
    fs.unlinkSync(filepath);
  }
}
