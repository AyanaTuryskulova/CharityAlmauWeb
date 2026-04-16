import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import {
  LISTING_NOT_FOUND,
  FAVORITE_ALREADY_EXISTS,
  FAVORITE_NOT_FOUND,
} from '../utils/errors';

const userSelect = {
  id: true,
  name: true,
  avatarUrl: true,
  rating: true,
};

export async function addFavorite(listingId: string, userId: string) {
  // Verify listing exists
  const listing = await prisma.listing.findUnique({ where: { id: listingId } });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }

  // Check if already favorited
  const existing = await prisma.favorite.findUnique({
    where: { userId_listingId: { userId, listingId } },
  });
  if (existing) {
    throw FAVORITE_ALREADY_EXISTS();
  }

  const favorite = await prisma.favorite.create({
    data: { userId, listingId },
  });

  return favorite;
}

export async function removeFavorite(listingId: string, userId: string) {
  const existing = await prisma.favorite.findUnique({
    where: { userId_listingId: { userId, listingId } },
  });
  if (!existing) {
    throw FAVORITE_NOT_FOUND();
  }

  await prisma.favorite.delete({
    where: { userId_listingId: { userId, listingId } },
  });
}

export async function getFavorites(query: { page?: string; limit?: string }, userId: string) {
  const { page, limit, skip } = getPagination(query);

  const where = { userId };

  const [favorites, total] = await Promise.all([
    prisma.favorite.findMany({
      where,
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: {
        listing: {
          include: {
            user: { select: userSelect },
            favorites: { where: { userId }, select: { id: true } },
            _count: { select: { favorites: true } },
          },
        },
      },
    }),
    prisma.favorite.count({ where }),
  ]);

  const data = favorites.map((fav) => {
    const { favorites: favs, ...rest } = fav.listing;
    return {
      ...rest,
      isFavorited: true,
    };
  });

  return { data, meta: buildMeta(page, limit, total) };
}
