import { Prisma } from '@prisma/client';
import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import { processListingImage, deleteImage } from '../utils/imageProcessing';
import {
  LISTING_NOT_FOUND,
  LISTING_NOT_OWNER,
} from '../utils/errors';

// Select for listing user embed
const userSelect = {
  id: true,
  name: true,
  avatarUrl: true,
  rating: true,
};

interface ListingsQuery {
  page?: string;
  limit?: string;
  type?: string;
  category?: string;
  search?: string;
  userId?: string;
  sort?: string;
}

export async function getListings(query: ListingsQuery, currentUserId?: string) {
  const { page, limit, skip } = getPagination(query);

  const where: Prisma.ListingWhereInput = { status: 'APPROVED' };

  if (query.type) {
    where.type = query.type as any;
  }
  if (query.category) {
    where.category = query.category as any;
  }
  if (query.userId) {
    where.userId = query.userId;
    // Owner can see their own listings in any status
    if (query.userId === currentUserId) {
      delete where.status;
    }
  }
  if (query.search) {
    where.AND = [
      {
        OR: [
          { title: { contains: query.search, mode: 'insensitive' } },
          { description: { contains: query.search, mode: 'insensitive' } },
        ],
      },
    ];
  }

  let orderBy: Prisma.ListingOrderByWithRelationInput[] = [{ createdAt: 'desc' }];
  if (query.sort === 'oldest') {
    orderBy = [{ createdAt: 'asc' }];
  }

  const [listings, total] = await Promise.all([
    prisma.listing.findMany({
      where,
      skip,
      take: limit,
      orderBy,
      include: {
        user: { select: userSelect },
        favorites: currentUserId
          ? { where: { userId: currentUserId }, select: { id: true } }
          : false,
        _count: { select: { favorites: true } },
      },
    }),
    prisma.listing.count({ where }),
  ]);

  const data = listings.map((listing) => {
    const { favorites, ...rest } = listing;
    return {
      ...rest,
      isFavorited: currentUserId ? (favorites as any[]).length > 0 : false,
    };
  });

  return { data, meta: buildMeta(page, limit, total) };
}

export async function getListingById(id: string, currentUserId?: string) {
  const listing = await prisma.listing.findUnique({
    where: { id },
    include: {
      user: { select: userSelect },
      favorites: currentUserId
        ? { where: { userId: currentUserId }, select: { id: true } }
        : false,
      _count: { select: { favorites: true } },
    },
  });

  if (!listing) {
    throw LISTING_NOT_FOUND();
  }

  const { favorites, ...rest } = listing;
  return {
    ...rest,
    isFavorited: currentUserId ? (favorites as any[]).length > 0 : false,
  };
}

interface CreateListingData {
  title: string;
  description: string;
  type: 'FREE' | 'EXCHANGE' | 'RENT';
  category: string;
  rentalPrice?: number;
  exchangeWish?: string;
  condition?: string;
}

export async function createListing(
  data: CreateListingData,
  files: Express.Multer.File[],
  userId: string
) {
  const images: string[] = [];
  for (const file of files) {
    const path = await processListingImage(file.buffer);
    images.push(path);
  }

  const listing = await prisma.listing.create({
    data: {
      title: data.title,
      description: data.description,
      type: data.type as any,
      category: data.category as any,
      rentalPrice: data.rentalPrice ? parseFloat(String(data.rentalPrice)) : null,
      exchangeWish: data.exchangeWish || null,
      condition: data.condition || null,
      images,
      userId,
    },
    include: {
      user: { select: userSelect },
      _count: { select: { favorites: true } },
    },
  });

  return { ...listing, isFavorited: false };
}

interface UpdateListingData {
  title?: string;
  description?: string;
  type?: 'FREE' | 'EXCHANGE' | 'RENT';
  category?: string;
  rentalPrice?: number;
  exchangeWish?: string;
  condition?: string;
  removeImages?: string[];
}

export async function updateListing(
  id: string,
  data: UpdateListingData,
  files: Express.Multer.File[],
  userId: string
) {
  const listing = await prisma.listing.findUnique({ where: { id } });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }
  if (listing.userId !== userId) {
    throw LISTING_NOT_OWNER();
  }

  let images = [...listing.images];

  // Remove specified images
  if (data.removeImages && data.removeImages.length > 0) {
    const toRemove = Array.isArray(data.removeImages) ? data.removeImages : [data.removeImages];
    for (const img of toRemove) {
      deleteImage(img);
      images = images.filter((i) => i !== img);
    }
  }

  // Add new images
  for (const file of files) {
    const path = await processListingImage(file.buffer);
    images.push(path);
  }

  const updateData: Prisma.ListingUpdateInput = { images };

  if (data.title !== undefined) updateData.title = data.title;
  if (data.description !== undefined) updateData.description = data.description;
  if (data.type !== undefined) updateData.type = data.type as any;
  if (data.category !== undefined) updateData.category = data.category as any;
  if (data.rentalPrice !== undefined) {
    updateData.rentalPrice = data.rentalPrice ? parseFloat(String(data.rentalPrice)) : null;
  }
  if (data.exchangeWish !== undefined) updateData.exchangeWish = data.exchangeWish || null;
  if (data.condition !== undefined) updateData.condition = data.condition || null;

  // Reset to pending if content changed
  if (data.title || data.description) {
    updateData.status = 'PENDING';
  }

  const updated = await prisma.listing.update({
    where: { id },
    data: updateData,
    include: {
      user: { select: userSelect },
      favorites: { where: { userId }, select: { id: true } },
      _count: { select: { favorites: true } },
    },
  });

  const { favorites, ...rest } = updated;
  return { ...rest, isFavorited: favorites.length > 0 };
}

export async function deleteListing(id: string, userId: string, role: string) {
  const listing = await prisma.listing.findUnique({ where: { id } });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }
  if (listing.userId !== userId && role !== 'ADMIN') {
    throw LISTING_NOT_OWNER();
  }

  // Delete images from disk
  for (const img of listing.images) {
    deleteImage(img);
  }

  await prisma.listing.delete({ where: { id } });
}

export async function getSimilarListings(id: string, currentUserId?: string) {
  const listing = await prisma.listing.findUnique({
    where: { id },
    select: { category: true },
  });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }

  const similar = await prisma.listing.findMany({
    where: {
      category: listing.category,
      id: { not: id },
      status: 'APPROVED',
    },
    take: 6,
    orderBy: { createdAt: 'desc' },
    include: {
      user: { select: userSelect },
      favorites: currentUserId
        ? { where: { userId: currentUserId }, select: { id: true } }
        : false,
      _count: { select: { favorites: true } },
    },
  });

  return similar.map((item) => {
    const { favorites, ...rest } = item;
    return {
      ...rest,
      isFavorited: currentUserId ? (favorites as any[]).length > 0 : false,
    };
  });
}
