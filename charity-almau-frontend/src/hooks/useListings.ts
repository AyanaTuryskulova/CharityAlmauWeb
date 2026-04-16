import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../types/listing';
import { listingsService } from '../services/listingsService';

interface UseListingsParams {
  page?: number;
  limit?: number;
  type?: string;
  category?: string;
  search?: string;
  userId?: string;
  sort?: string;
}

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export function useListings(params: UseListingsParams = {}) {
  const { t } = useTranslation();
  const [listings, setListings] = useState<Listing[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const key = JSON.stringify(params);

  const fetchListings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listingsService.getListings(params);
      setListings(res.data);
      setMeta(res.meta ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    fetchListings();
  }, [fetchListings]);

  return { listings, meta, loading, error, refetch: fetchListings };
}
