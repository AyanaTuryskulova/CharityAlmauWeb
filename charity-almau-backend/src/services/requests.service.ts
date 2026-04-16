import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import {
  LISTING_NOT_FOUND,
  LISTING_NOT_APPROVED,
  REQUEST_NOT_FOUND,
  REQUEST_ALREADY_EXISTS,
  REQUEST_OWN_LISTING,
  REQUEST_NOT_PENDING,
  FORBIDDEN,
} from '../utils/errors';

const userSelect = {
  id: true,
  name: true,
  avatarUrl: true,
  rating: true,
};

const requestInclude = {
  listing: { select: { id: true, title: true, images: true } },
  sender: { select: userSelect },
  receiver: { select: userSelect },
};

export async function createRequest(
  data: { listingId: string; message?: string },
  senderId: string,
) {
  const listing = await prisma.listing.findUnique({ where: { id: data.listingId } });
  if (!listing) throw LISTING_NOT_FOUND();
  if (listing.status !== 'APPROVED') throw LISTING_NOT_APPROVED();
  if (listing.userId === senderId) throw REQUEST_OWN_LISTING();

  const existing = await prisma.request.findUnique({
    where: { senderId_listingId: { senderId, listingId: data.listingId } },
  });
  if (existing) throw REQUEST_ALREADY_EXISTS();

  const request = await prisma.request.create({
    data: {
      listingId: data.listingId,
      message: data.message || null,
      senderId,
      receiverId: listing.userId,
    },
    include: requestInclude,
  });

  return request;
}

export async function getIncomingRequests(
  query: { page?: string; limit?: string; status?: string },
  userId: string,
) {
  const { page, limit, skip } = getPagination(query);

  const where: any = { receiverId: userId };
  if (query.status) {
    where.status = query.status;
  }

  const [requests, total] = await Promise.all([
    prisma.request.findMany({
      where,
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: requestInclude,
    }),
    prisma.request.count({ where }),
  ]);

  return { data: requests, meta: buildMeta(page, limit, total) };
}

export async function getOutgoingRequests(
  query: { page?: string; limit?: string; status?: string },
  userId: string,
) {
  const { page, limit, skip } = getPagination(query);

  const where: any = { senderId: userId };
  if (query.status) {
    where.status = query.status;
  }

  const [requests, total] = await Promise.all([
    prisma.request.findMany({
      where,
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
      include: requestInclude,
    }),
    prisma.request.count({ where }),
  ]);

  return { data: requests, meta: buildMeta(page, limit, total) };
}

export async function acceptRequest(requestId: string, userId: string) {
  const request = await prisma.request.findUnique({
    where: { id: requestId },
    include: requestInclude,
  });
  if (!request) throw REQUEST_NOT_FOUND();
  if (request.receiverId !== userId) throw FORBIDDEN();
  if (request.status !== 'PENDING') throw REQUEST_NOT_PENDING();

  const updated = await prisma.request.update({
    where: { id: requestId },
    data: { status: 'ACCEPTED' },
    include: requestInclude,
  });

  return updated;
}

export async function rejectRequest(requestId: string, userId: string) {
  const request = await prisma.request.findUnique({
    where: { id: requestId },
    include: requestInclude,
  });
  if (!request) throw REQUEST_NOT_FOUND();
  if (request.receiverId !== userId) throw FORBIDDEN();
  if (request.status !== 'PENDING') throw REQUEST_NOT_PENDING();

  const updated = await prisma.request.update({
    where: { id: requestId },
    data: { status: 'REJECTED' },
    include: requestInclude,
  });

  return updated;
}

export async function cancelRequest(requestId: string, userId: string) {
  const request = await prisma.request.findUnique({
    where: { id: requestId },
    include: requestInclude,
  });
  if (!request) throw REQUEST_NOT_FOUND();
  if (request.senderId !== userId) throw FORBIDDEN();
  if (request.status !== 'PENDING') throw REQUEST_NOT_PENDING();

  const updated = await prisma.request.update({
    where: { id: requestId },
    data: { status: 'CANCELLED' },
    include: requestInclude,
  });

  return updated;
}
