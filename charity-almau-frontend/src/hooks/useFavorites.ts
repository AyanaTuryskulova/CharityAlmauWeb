import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../types/listing';
import { favoritesService } from '../services/favoritesService';

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export function useFavorites(params: { page?: number; limit?: number } = {}) {
  const { t } = useTranslation();
  const [favorites, setFavorites] = useState<Listing[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const key = JSON.stringify(params);

  const fetchFavorites = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await favoritesService.getFavorites(params);
      setFavorites(res.data);
      setMeta(res.meta ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    fetchFavorites();
  }, [fetchFavorites]);

  const toggleFavorite = useCallback(async (listingId: string, isFavorited: boolean) => {
    try {
      if (isFavorited) {
        await favoritesService.removeFavorite(listingId);
        setFavorites((prev) => prev.filter((l) => l.id !== listingId));
      } else {
        await favoritesService.addFavorite(listingId);
      }
    } catch {
      // silently fail, could add toast here
    }
  }, []);

  return { favorites, meta, loading, error, refetch: fetchFavorites, toggleFavorite };
}
