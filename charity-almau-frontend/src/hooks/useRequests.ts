import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Request } from '../types/request';
import { requestsService } from '../services/requestsService';

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

type Tab = 'incoming' | 'outgoing';

export function useRequests(tab: Tab, params: { page?: number; limit?: number } = {}) {
  const { t } = useTranslation();
  const [requests, setRequests] = useState<Request[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const key = `${tab}-${JSON.stringify(params)}`;

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetcher = tab === 'incoming'
        ? requestsService.getIncoming
        : requestsService.getOutgoing;
      const res = await fetcher(params);
      setRequests(res.data);
      setMeta(res.meta ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const acceptRequest = useCallback(async (id: string) => {
    await requestsService.acceptRequest(id);
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'ACCEPTED' as const } : r))
    );
  }, []);

  const rejectRequest = useCallback(async (id: string) => {
    await requestsService.rejectRequest(id);
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'REJECTED' as const } : r))
    );
  }, []);

  const cancelRequest = useCallback(async (id: string) => {
    await requestsService.cancelRequest(id);
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'CANCELLED' as const } : r))
    );
  }, []);

  return {
    requests,
    meta,
    loading,
    error,
    refetch: fetchRequests,
    acceptRequest,
    rejectRequest,
    cancelRequest,
  };
}
