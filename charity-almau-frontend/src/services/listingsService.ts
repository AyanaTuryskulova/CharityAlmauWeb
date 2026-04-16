import api from './api';
import type { Listing } from '../types/listing';
import type { ApiResponse } from '../types/api';

interface ListingsParams {
  page?: number;
  limit?: number;
  type?: string;
  category?: string;
  search?: string;
  userId?: string;
  sort?: string;
}

export const listingsService = {
  async getListings(params: ListingsParams = {}): Promise<ApiResponse<Listing[]>> {
    return api.get('/listings', { params });
  },

  async getListing(id: string): Promise<ApiResponse<Listing>> {
    return api.get(`/listings/${id}`);
  },

  async getSimilar(id: string): Promise<ApiResponse<Listing[]>> {
    return api.get(`/listings/${id}/similar`);
  },

  async createListing(formData: FormData): Promise<ApiResponse<Listing>> {
    return api.post('/listings', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  async updateListing(id: string, formData: FormData): Promise<ApiResponse<Listing>> {
    return api.put(`/listings/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  async deleteListing(id: string): Promise<void> {
    return api.delete(`/listings/${id}`);
  },
};
