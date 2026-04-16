import api from './api';
import type { Listing } from '../types/listing';
import type { ApiResponse } from '../types/api';

interface FavoritesParams {
  page?: number;
  limit?: number;
}

export const favoritesService = {
  async getFavorites(params: FavoritesParams = {}): Promise<ApiResponse<Listing[]>> {
    return api.get('/favorites', { params });
  },

  async addFavorite(listingId: string): Promise<void> {
    return api.post('/favorites', { listingId });
  },

  async removeFavorite(listingId: string): Promise<void> {
    return api.delete(`/favorites/${listingId}`);
  },
};
