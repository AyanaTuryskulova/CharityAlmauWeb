import { io, type Socket } from 'socket.io-client';
import { WS_URL } from '../constants';
import type { Message } from '../types/chat';

let socket: Socket | null = null;

export const socketService = {
  connect(token: string) {
    if (socket?.connected) return;
    socket = io(WS_URL, { auth: { token: `Bearer ${token}` } });
  },

  disconnect() {
    socket?.disconnect();
    socket = null;
  },

  joinRoom(roomId: string) {
    socket?.emit('chat:join', { roomId });
  },

  leaveRoom(roomId: string) {
    socket?.emit('chat:leave', { roomId });
  },

  sendMessage(roomId: string, text: string) {
    socket?.emit('chat:message', { roomId, text });
  },

  startTyping(roomId: string) {
    socket?.emit('chat:typing', { roomId });
  },

  stopTyping(roomId: string) {
    socket?.emit('chat:stop-typing', { roomId });
  },

  markRead(roomId: string) {
    socket?.emit('chat:read', { roomId });
  },

  onMessage(callback: (message: Message) => void) {
    socket?.on('chat:message', callback);
    return () => { socket?.off('chat:message', callback); };
  },

  onTyping(callback: (data: { roomId: string; userId: string }) => void) {
    socket?.on('chat:typing', callback);
    return () => { socket?.off('chat:typing', callback); };
  },

  onStopTyping(callback: (data: { roomId: string; userId: string }) => void) {
    socket?.on('chat:stop-typing', callback);
    return () => { socket?.off('chat:stop-typing', callback); };
  },

  onRead(callback: (data: { roomId: string; userId: string }) => void) {
    socket?.on('chat:read', callback);
    return () => { socket?.off('chat:read', callback); };
  },

  onRequestNotification(callback: (data: { requestId: string; listingId: string; listingTitle: string; senderName: string; type: string }) => void) {
    socket?.on('notification:request', callback);
    return () => { socket?.off('notification:request', callback); };
  },

  onListingNotification(callback: (data: { listingId: string; listingTitle: string; type: string; rejectReason?: string }) => void) {
    socket?.on('notification:listing', callback);
    return () => { socket?.off('notification:listing', callback); };
  },
};
