import api from './api';
import type { ChatRoom, Message } from '../types/chat';
import type { ApiResponse } from '../types/api';

export const chatService = {
  async getRooms(): Promise<ChatRoom[]> {
    const res = await api.get('/chat/rooms') as unknown as ApiResponse<ChatRoom[]>;
    return res.data;
  },

  async createRoom(otherUserId: string, listingId?: string): Promise<ChatRoom> {
    const res = await api.post('/chat/rooms', { otherUserId, listingId }) as unknown as ApiResponse<ChatRoom>;
    return res.data;
  },

  async getMessages(roomId: string, params?: { page?: number; limit?: number }): Promise<{ data: Message[]; meta: { page: number; limit: number; total: number; totalPages: number } }> {
    const res = await api.get(`/chat/rooms/${roomId}/messages`, { params }) as unknown as ApiResponse<Message[]>;
    return { data: res.data, meta: res.meta! };
  },

  async markRead(roomId: string): Promise<void> {
    await api.post(`/chat/rooms/${roomId}/read`);
  },
};
