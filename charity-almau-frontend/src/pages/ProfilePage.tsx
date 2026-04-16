import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { listingsService } from '../services/listingsService';
import { favoritesService } from '../services/favoritesService';
import { userService } from '../services/userService';
import type { Listing } from '../types/listing';
import type { Rating } from '../types/rating';
import ProfileHeader from '../components/profile/ProfileHeader';
import ProfileTabs from '../components/profile/ProfileTabs';
import Loader from '../components/common/Loader';
import styles from './ProfilePage.module.css';

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export default function ProfilePage() {
  const { t } = useTranslation('profile');
  const { user } = useAuth();
  const navigate = useNavigate();

  const [listings, setListings] = useState<Listing[]>([]);
  const [listingsMeta, setListingsMeta] = useState<Meta | null>(null);
  const [listingsLoading, setListingsLoading] = useState(true);
  const [listingsError, setListingsError] = useState<string | null>(null);
  const [listingsPage, setListingsPage] = useState(1);

  const [favorites, setFavorites] = useState<Listing[]>([]);
  const [favoritesMeta, setFavoritesMeta] = useState<Meta | null>(null);
  const [favoritesLoading, setFavoritesLoading] = useState(true);
  const [favoritesError, setFavoritesError] = useState<string | null>(null);
  const [favoritesPage, setFavoritesPage] = useState(1);

  const [ratings, setRatings] = useState<Rating[]>([]);
  const [ratingsMeta, setRatingsMeta] = useState<Meta | null>(null);
  const [ratingsLoading, setRatingsLoading] = useState(true);
  const [ratingsError, setRatingsError] = useState<string | null>(null);
  const [ratingsPage, setRatingsPage] = useState(1);

  const fetchListings = useCallback(async () => {
    if (!user) return;
    setListingsLoading(true);
    setListingsError(null);
    try {
      const res = await listingsService.getListings({ userId: user.id, page: listingsPage, limit: 10 });
      setListings(res.data);
      setListingsMeta(res.meta ?? null);
    } catch (err: unknown) {
      setListingsError(err instanceof Error ? err.message : t('common:error'));
    } finally {
      setListingsLoading(false);
    }
  }, [user, listingsPage, t]);

  const fetchFavorites = useCallback(async () => {
    setFavoritesLoading(true);
    setFavoritesError(null);
    try {
      const res = await favoritesService.getFavorites({ page: favoritesPage, limit: 10 });
      setFavorites(res.data);
      setFavoritesMeta(res.meta ?? null);
    } catch (err: unknown) {
      setFavoritesError(err instanceof Error ? err.message : t('common:error'));
    } finally {
      setFavoritesLoading(false);
    }
  }, [favoritesPage, t]);

  const fetchRatings = useCallback(async () => {
    if (!user) return;
    setRatingsLoading(true);
    setRatingsError(null);
    try {
      const res = await userService.getRatings(user.id, { page: ratingsPage, limit: 10 });
      setRatings(res.data);
      setRatingsMeta(res.meta ?? null);
    } catch (err: unknown) {
      setRatingsError(err instanceof Error ? err.message : t('common:error'));
    } finally {
      setRatingsLoading(false);
    }
  }, [user, ratingsPage, t]);

  useEffect(() => { fetchListings(); }, [fetchListings]);
  useEffect(() => { fetchFavorites(); }, [fetchFavorites]);
  useEffect(() => { fetchRatings(); }, [fetchRatings]);

  if (!user) return <Loader fullPage />;

  return (
    <div className={styles.page}>
      <h2 className={styles.pageTitle}>{t('title')}</h2>

      <ProfileHeader
        user={user}
        isOwn
        onEdit={() => navigate('/profile/edit')}
      />

      <ProfileTabs
        listings={listings}
        listingsMeta={listingsMeta}
        onListingsPageChange={setListingsPage}
        listingsLoading={listingsLoading}
        listingsError={listingsError}
        onRetryListings={fetchListings}
        favorites={favorites}
        favoritesMeta={favoritesMeta}
        onFavoritesPageChange={setFavoritesPage}
        favoritesLoading={favoritesLoading}
        favoritesError={favoritesError}
        onRetryFavorites={fetchFavorites}
        ratings={ratings}
        ratingsMeta={ratingsMeta}
        onRatingsPageChange={setRatingsPage}
        ratingsLoading={ratingsLoading}
        ratingsError={ratingsError}
        onRetryRatings={fetchRatings}
        showFavorites
      />
    </div>
  );
}
