import api from './api';
import type { Request } from '../types/request';
import type { ApiResponse } from '../types/api';

interface RequestsParams {
  page?: number;
  limit?: number;
}

export const requestsService = {
  async createRequest(listingId: string, message?: string): Promise<Request> {
    return api.post('/requests', { listingId, message });
  },

  async getIncoming(params: RequestsParams = {}): Promise<ApiResponse<Request[]>> {
    return api.get('/requests/incoming', { params });
  },

  async getOutgoing(params: RequestsParams = {}): Promise<ApiResponse<Request[]>> {
    return api.get('/requests/outgoing', { params });
  },

  async acceptRequest(id: string): Promise<Request> {
    return api.patch(`/requests/${id}/accept`);
  },

  async rejectRequest(id: string): Promise<Request> {
    return api.patch(`/requests/${id}/reject`);
  },

  async cancelRequest(id: string): Promise<Request> {
    return api.patch(`/requests/${id}/cancel`);
  },
};
