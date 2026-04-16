import api from './api';
import type { User } from '../types/user';
import type { Rating } from '../types/rating';
import type { ApiResponse } from '../types/api';

interface RatingsParams {
  page?: number;
  limit?: number;
}

export const userService = {
  async getUser(id: string): Promise<ApiResponse<User>> {
    return api.get(`/users/${id}`);
  },

  async updateMe(formData: FormData): Promise<ApiResponse<User>> {
    return api.put('/users/me', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  async getRatings(userId: string, params: RatingsParams = {}): Promise<ApiResponse<Rating[]>> {
    return api.get(`/users/${userId}/ratings`, { params });
  },

  async postRating(
    userId: string,
    score: number,
    comment?: string,
    listingId?: string
  ): Promise<ApiResponse<Rating>> {
    return api.post(`/users/${userId}/ratings`, { score, comment, listingId });
  },
};
