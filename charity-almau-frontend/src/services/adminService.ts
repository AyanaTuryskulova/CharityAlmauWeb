import api from './api';
import type { Listing } from '../types/listing';

export interface AdminStats {
  totalUsers: number;
  totalListings: number;
  pendingListings: number;
}

interface PaginatedListings {
  data: Listing[];
  meta: { page: number; limit: number; total: number; totalPages: number };
}

export const adminService = {
  async getPendingListings(params?: { page?: number; limit?: number }): Promise<PaginatedListings> {
    const res = await api.get<PaginatedListings>('/admin/listings', { params });
    return (res as unknown as { data?: PaginatedListings }).data ?? res as unknown as PaginatedListings;
  },

  async approveListing(id: string): Promise<Listing> {
    const res = await api.patch<Listing>(`/admin/listings/${id}/approve`);
    return (res as unknown as { data?: Listing }).data ?? res as unknown as Listing;
  },

  async rejectListing(id: string, reason: string): Promise<Listing> {
    const res = await api.patch<Listing>(`/admin/listings/${id}/reject`, { reason });
    return (res as unknown as { data?: Listing }).data ?? res as unknown as Listing;
  },

  async getStats(): Promise<AdminStats> {
    const res = await api.get<AdminStats>('/admin/stats');
    return (res as unknown as { data?: AdminStats }).data ?? res as unknown as AdminStats;
  },
};
