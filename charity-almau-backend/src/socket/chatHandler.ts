import { Server, Socket } from 'socket.io';
import { JwtPayload } from '../types';
import * as chatService from '../services/chat.service';

export function registerChatHandlers(io: Server, socket: Socket, user: JwtPayload) {
  // Join a chat room
  socket.on('chat:join', async ({ roomId }: { roomId: string }) => {
    const members = await chatService.getRoomMemberIds(roomId);
    if (!members || !members.includes(user.userId)) return;
    socket.join(`chatroom:${roomId}`);
  });

  // Leave a chat room
  socket.on('chat:leave', ({ roomId }: { roomId: string }) => {
    socket.leave(`chatroom:${roomId}`);
  });

  // Send a message
  socket.on('chat:message', async ({ roomId, text }: { roomId: string; text: string }) => {
    if (!text || !text.trim()) return;

    try {
      const message = await chatService.createMessage(roomId, text.trim(), user.userId);

      // Emit to all room members
      io.to(`chatroom:${roomId}`).emit('chat:message', {
        id: message.id,
        text: message.text,
        senderId: message.senderId,
        chatRoomId: message.chatRoomId,
        createdAt: message.createdAt,
        isRead: message.isRead,
      });

      // Also notify the other user via their personal room (for badge updates)
      const members = await chatService.getRoomMemberIds(roomId);
      if (members) {
        const otherUserId = members.find((id) => id !== user.userId);
        if (otherUserId) {
          io.to(`user:${otherUserId}`).emit('chat:message', {
            id: message.id,
            text: message.text,
            senderId: message.senderId,
            chatRoomId: message.chatRoomId,
            createdAt: message.createdAt,
            isRead: message.isRead,
          });
        }
      }
    } catch {
      // Silently fail — socket errors don't need HTTP error responses
    }
  });

  // Typing indicator
  socket.on('chat:typing', ({ roomId }: { roomId: string }) => {
    socket.to(`chatroom:${roomId}`).emit('chat:typing', { roomId, userId: user.userId });
  });

  // Stop typing indicator
  socket.on('chat:stop-typing', ({ roomId }: { roomId: string }) => {
    socket.to(`chatroom:${roomId}`).emit('chat:stop-typing', { roomId, userId: user.userId });
  });

  // Mark messages as read
  socket.on('chat:read', async ({ roomId }: { roomId: string }) => {
    try {
      await chatService.markAsRead(roomId, user.userId);
      socket.to(`chatroom:${roomId}`).emit('chat:read', { roomId, userId: user.userId });
    } catch {
      // Silently fail
    }
  });
}
