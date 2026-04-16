import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import { processAvatarImage } from '../utils/imageProcessing';
import {
  USER_NOT_FOUND,
  RATING_ALREADY_EXISTS,
  RATING_SELF,
  RATING_INVALID_SCORE,
} from '../utils/errors';

const userSelect = {
  id: true,
  email: true,
  name: true,
  avatarUrl: true,
  role: true,
  rating: true,
  ratingCount: true,
  createdAt: true,
  _count: { select: { listings: true } },
};

const ratingInclude = {
  author: { select: { id: true, name: true, avatarUrl: true } },
};

export async function getUserById(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: userSelect,
  });
  if (!user) throw USER_NOT_FOUND();
  return user;
}

export async function updateProfile(
  userId: string,
  data: { name?: string },
  avatarFile?: Express.Multer.File,
) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw USER_NOT_FOUND();

  const updateData: any = {};
  if (data.name) updateData.name = data.name;
  if (avatarFile) {
    updateData.avatarUrl = await processAvatarImage(avatarFile.buffer);
  }

  const updated = await prisma.user.update({
    where: { id: userId },
    select: userSelect,
  data: updateData,
  });

  return updated;
}

export async function getUserRatings(
  targetId: string,
  query: { page?: string; limit?: string },
) {
  const user = await prisma.user.findUnique({ where: { id: targetId } });
  if (!user) throw USER_NOT_FOUND();

  const { page, limit, skip } = getPagination(query);

  const where = { targetId };

  const [ratings, total] = await Promise.all([
    prisma.rating.findMany({
      where,
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: ratingInclude,
    }),
    prisma.rating.count({ where }),
  ]);

  return { data: ratings, meta: buildMeta(page, limit, total) };
}

export async function createRating(
  targetId: string,
  authorId: string,
  data: { score: number; comment?: string; listingId?: string },
) {
  if (targetId === authorId) throw RATING_SELF();
  if (data.score < 1 || data.score > 5) throw RATING_INVALID_SCORE();

  const target = await prisma.user.findUnique({ where: { id: targetId } });
  if (!target) throw USER_NOT_FOUND();

  // Check for duplicate rating (handle nullable listingId)
  const existing = data.listingId
    ? await prisma.rating.findUnique({
        where: {
          authorId_targetId_listingId: {
            authorId,
            targetId,
            listingId: data.listingId,
          },
        },
      })
    : await prisma.rating.findFirst({
        where: { authorId, targetId, listingId: null },
      });
  if (existing) throw RATING_ALREADY_EXISTS();

  // Create rating and recalculate user rating in a transaction
  const rating = await prisma.$transaction(async (tx) => {
    const created = await tx.rating.create({
      data: {
        score: data.score,
        comment: data.comment || null,
        authorId,
        targetId,
        listingId: data.listingId || null,
      },
      include: ratingInclude,
    });

    const agg = await tx.rating.aggregate({
      where: { targetId },
      _avg: { score: true },
      _count: { score: true },
    });

    await tx.user.update({
      where: { id: targetId },
      data: {
        rating: agg._avg.score || 0,
        ratingCount: agg._count.score,
      },
    });

    return created;
  });

  return rating;
}
