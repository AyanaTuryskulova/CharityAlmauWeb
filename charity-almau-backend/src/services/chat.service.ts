import prisma from '../config/prisma';
import { getPagination, buildMeta } from '../utils/pagination';
import { CHATROOM_NOT_FOUND, CHATROOM_NOT_MEMBER, USER_NOT_FOUND } from '../utils/errors';

const userSelect = {
  id: true,
  name: true,
  avatarUrl: true,
  rating: true,
};

export async function getChatRooms(userId: string) {
  const rooms = await prisma.chatRoom.findMany({
    where: {
      OR: [{ user1Id: userId }, { user2Id: userId }],
    },
    include: {
      user1: { select: userSelect },
      user2: { select: userSelect },
      messages: {
        orderBy: { createdAt: 'desc' },
        take: 1,
      },
    },
    orderBy: { updatedAt: 'desc' },
  });

  const roomIds = rooms.map((r) => r.id);

  // Count unread messages per room in one query
  const unreadCounts = await prisma.message.groupBy({
    by: ['chatRoomId'],
    where: {
      chatRoomId: { in: roomIds },
      senderId: { not: userId },
      isRead: false,
    },
    _count: true,
  });

  const unreadMap = new Map(unreadCounts.map((u) => [u.chatRoomId, u._count]));

  // Fetch listing info for rooms that have a listingId
  const listingIds = rooms.map((r) => r.listingId).filter(Boolean) as string[];
  const listings = listingIds.length
    ? await prisma.listing.findMany({
        where: { id: { in: listingIds } },
        select: { id: true, title: true, images: true },
      })
    : [];
  const listingMap = new Map(listings.map((l) => [l.id, l]));

  return rooms.map((room) => {
    const otherUser = room.user1Id === userId ? room.user2 : room.user1;
    const lastMessage = room.messages[0] || null;

    return {
      id: room.id,
      listingId: room.listingId,
      createdAt: room.createdAt,
      updatedAt: room.updatedAt,
      otherUser,
      listing: room.listingId ? listingMap.get(room.listingId) || null : null,
      lastMessage: lastMessage
        ? {
            id: lastMessage.id,
            text: lastMessage.text,
            senderId: lastMessage.senderId,
            createdAt: lastMessage.createdAt,
            isRead: lastMessage.isRead,
          }
        : null,
      unreadCount: unreadMap.get(room.id) || 0,
    };
  });
}

export async function createOrGetChatRoom(
  data: { otherUserId: string; listingId?: string },
  userId: string,
) {
  const otherUser = await prisma.user.findUnique({ where: { id: data.otherUserId } });
  if (!otherUser) throw USER_NOT_FOUND();

  // Normalize user order so unique constraint works both ways
  const [u1, u2] = [userId, data.otherUserId].sort();

  const existing = await prisma.chatRoom.findFirst({
    where: {
      user1Id: u1,
      user2Id: u2,
      listingId: data.listingId || null,
    },
  });

  if (existing) {
    return formatChatRoom(existing.id, userId);
  }

  const room = await prisma.chatRoom.create({
    data: {
      user1Id: u1,
      user2Id: u2,
      listingId: data.listingId || null,
    },
  });

  return formatChatRoom(room.id, userId);
}

async function formatChatRoom(roomId: string, userId: string) {
  const room = await prisma.chatRoom.findUnique({
    where: { id: roomId },
    include: {
      user1: { select: userSelect },
      user2: { select: userSelect },
      messages: {
        orderBy: { createdAt: 'desc' },
        take: 1,
      },
    },
  });

  if (!room) throw CHATROOM_NOT_FOUND();

  const listing = room.listingId
    ? await prisma.listing.findUnique({
        where: { id: room.listingId },
        select: { id: true, title: true, images: true },
      })
    : null;

  const unreadCount = await prisma.message.count({
    where: {
      chatRoomId: roomId,
      senderId: { not: userId },
      isRead: false,
    },
  });

  const otherUser = room.user1Id === userId ? room.user2 : room.user1;
  const lastMessage = room.messages[0] || null;

  return {
    id: room.id,
    listingId: room.listingId,
    createdAt: room.createdAt,
    updatedAt: room.updatedAt,
    otherUser,
    listing,
    lastMessage: lastMessage
      ? {
          id: lastMessage.id,
          text: lastMessage.text,
          senderId: lastMessage.senderId,
          createdAt: lastMessage.createdAt,
          isRead: lastMessage.isRead,
        }
      : null,
    unreadCount,
  };
}

export async function getMessages(
  roomId: string,
  query: { page?: string; limit?: string },
  userId: string,
) {
  const room = await prisma.chatRoom.findUnique({ where: { id: roomId } });
  if (!room) throw CHATROOM_NOT_FOUND();
  if (room.user1Id !== userId && room.user2Id !== userId) throw CHATROOM_NOT_MEMBER();

  const { page, limit, skip } = getPagination(query);

  const [messages, total] = await Promise.all([
    prisma.message.findMany({
      where: { chatRoomId: roomId },
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.message.count({ where: { chatRoomId: roomId } }),
  ]);

  return { data: messages, meta: buildMeta(page, limit, total) };
}

export async function markAsRead(roomId: string, userId: string) {
  const room = await prisma.chatRoom.findUnique({ where: { id: roomId } });
  if (!room) throw CHATROOM_NOT_FOUND();
  if (room.user1Id !== userId && room.user2Id !== userId) throw CHATROOM_NOT_MEMBER();

  const result = await prisma.message.updateMany({
    where: {
      chatRoomId: roomId,
      senderId: { not: userId },
      isRead: false,
    },
    data: { isRead: true },
  });

  return { updatedCount: result.count };
}

export async function createMessage(roomId: string, text: string, senderId: string) {
  const room = await prisma.chatRoom.findUnique({ where: { id: roomId } });
  if (!room) throw CHATROOM_NOT_FOUND();
  if (room.user1Id !== senderId && room.user2Id !== senderId) throw CHATROOM_NOT_MEMBER();

  const [message] = await prisma.$transaction([
    prisma.message.create({
      data: {
        text,
        senderId,
        chatRoomId: roomId,
      },
    }),
    prisma.chatRoom.update({
      where: { id: roomId },
      data: { updatedAt: new Date() },
    }),
  ]);

  return message;
}

export async function getRoomMemberIds(roomId: string): Promise<[string, string] | null> {
  const room = await prisma.chatRoom.findUnique({
    where: { id: roomId },
    select: { user1Id: true, user2Id: true },
  });
  if (!room) return null;
  return [room.user1Id, room.user2Id];
}
