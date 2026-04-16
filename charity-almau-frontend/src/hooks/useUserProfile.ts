import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import type { User } from '../types/user';
import type { Rating } from '../types/rating';
import { userService } from '../services/userService';

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export function useUserProfile(userId: string | undefined) {
  const { t } = useTranslation();
  const [user, setUser] = useState<User | null>(null);
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [ratingsMeta, setRatingsMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [ratingsLoading, setRatingsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await userService.getUser(userId);
      setUser(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setLoading(false);
    }
  }, [userId, t]);

  const fetchRatings = useCallback(async (page = 1) => {
    if (!userId) return;
    setRatingsLoading(true);
    try {
      const res = await userService.getRatings(userId, { page, limit: 10 });
      setRatings(res.data);
      setRatingsMeta(res.meta ?? null);
    } catch {
      // silent
    } finally {
      setRatingsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUser();
    fetchRatings();
  }, [fetchUser, fetchRatings]);

  return {
    user,
    ratings,
    ratingsMeta,
    loading,
    ratingsLoading,
    error,
    refetchUser: fetchUser,
    refetchRatings: fetchRatings,
  };
}
