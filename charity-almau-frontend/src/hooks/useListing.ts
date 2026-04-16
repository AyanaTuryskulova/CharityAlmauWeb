import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../types/listing';
import { listingsService } from '../services/listingsService';

export function useListing(id: string | undefined) {
  const { t } = useTranslation();
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchListing = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listingsService.getListing(id);
      setListing(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    fetchListing();
  }, [fetchListing]);

  return { listing, loading, error, refetch: fetchListing };
}
