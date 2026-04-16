import { Prisma } from '@prisma/client';
import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import { LISTING_NOT_FOUND } from '../utils/errors';
import { getIO } from '../socket';

const userSelect = {
  id: true,
  name: true,
  avatarUrl: true,
  rating: true,
};

interface AdminListingsQuery {
  page?: string;
  limit?: string;
  status?: string;
}

export async function getListings(query: AdminListingsQuery) {
  const { page, limit, skip } = getPagination(query);

  const where: Prisma.ListingWhereInput = {};
  if (query.status) {
    where.status = query.status as any;
  }

  const [listings, total] = await Promise.all([
    prisma.listing.findMany({
      where,
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: {
        user: { select: userSelect },
        _count: { select: { favorites: true } },
      },
    }),
    prisma.listing.count({ where }),
  ]);

  const data = listings.map((listing) => ({
    ...listing,
    isFavorited: false,
  }));

  return { data, meta: buildMeta(page, limit, total) };
}

export async function approveListing(id: string) {
  const listing = await prisma.listing.findUnique({ where: { id } });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }

  const updated = await prisma.listing.update({
    where: { id },
    data: { status: 'APPROVED', rejectReason: null },
    include: {
      user: { select: userSelect },
      _count: { select: { favorites: true } },
    },
  });

  // Notify listing owner
  try {
    const io = getIO();
    io.to(`user:${listing.userId}`).emit('notification:listing', {
      listingId: listing.id,
      listingTitle: listing.title,
      type: 'APPROVED',
    });
  } catch {
    // Socket not initialized — skip notification
  }

  return { ...updated, isFavorited: false };
}

export async function rejectListing(id: string, reason: string) {
  const listing = await prisma.listing.findUnique({ where: { id } });
  if (!listing) {
    throw LISTING_NOT_FOUND();
  }

  const updated = await prisma.listing.update({
    where: { id },
    data: { status: 'REJECTED', rejectReason: reason },
    include: {
      user: { select: userSelect },
      _count: { select: { favorites: true } },
    },
  });

  // Notify listing owner
  try {
    const io = getIO();
    io.to(`user:${listing.userId}`).emit('notification:listing', {
      listingId: listing.id,
      listingTitle: listing.title,
      type: 'REJECTED',
      rejectReason: reason,
    });
  } catch {
    // Socket not initialized — skip notification
  }

  return { ...updated, isFavorited: false };
}

export async function getStats() {
  const [
    totalUsers,
    totalListings,
    pendingListings,
    approvedListings,
    rejectedListings,
    closedListings,
    totalRequests,
    pendingRequests,
    totalMessages,
    totalRatings,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.listing.count(),
    prisma.listing.count({ where: { status: 'PENDING' } }),
    prisma.listing.count({ where: { status: 'APPROVED' } }),
    prisma.listing.count({ where: { status: 'REJECTED' } }),
    prisma.listing.count({ where: { status: 'CLOSED' } }),
    prisma.request.count(),
    prisma.request.count({ where: { status: 'PENDING' } }),
    prisma.message.count(),
    prisma.rating.count(),
  ]);

  return {
    users: { total: totalUsers },
    listings: {
      total: totalListings,
      pending: pendingListings,
      approved: approvedListings,
      rejected: rejectedListings,
      closed: closedListings,
    },
    requests: {
      total: totalRequests,
      pending: pendingRequests,
    },
    messages: { total: totalMessages },
    ratings: { total: totalRatings },
  };
}
