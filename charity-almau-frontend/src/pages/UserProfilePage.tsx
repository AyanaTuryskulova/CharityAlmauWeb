import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import { listingsService } from '../services/listingsService';
import { userService } from '../services/userService';
import { chatService } from '../services/chatService';
import type { Listing } from '../types/listing';
import ProfileHeader from '../components/profile/ProfileHeader';
import ProfileTabs from '../components/profile/ProfileTabs';
import ReviewForm from '../components/profile/ReviewForm';
import Loader from '../components/common/Loader';
import ErrorState from '../components/common/ErrorState';
import styles from './UserProfilePage.module.css';

interface Meta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export default function UserProfilePage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const { user, ratings, ratingsMeta, loading, ratingsLoading, error, refetchUser, refetchRatings } = useUserProfile(userId);

  const [listings, setListings] = useState<Listing[]>([]);
  const [listingsMeta, setListingsMeta] = useState<Meta | null>(null);
  const [listingsLoading, setListingsLoading] = useState(true);
  const [listingsError, setListingsError] = useState<string | null>(null);
  const [listingsPage, setListingsPage] = useState(1);
  const [ratingsPage, setRatingsPage] = useState(1);

  const fetchListings = useCallback(async () => {
    if (!userId) return;
    setListingsLoading(true);
    setListingsError(null);
    try {
      const res = await listingsService.getListings({ userId, page: listingsPage, limit: 10 });
      setListings(res.data);
      setListingsMeta(res.meta ?? null);
    } catch (err: unknown) {
      setListingsError(err instanceof Error ? err.message : 'Error');
    } finally {
      setListingsLoading(false);
    }
  }, [userId, listingsPage]);

  useEffect(() => { fetchListings(); }, [fetchListings]);

  useEffect(() => {
    if (ratingsPage > 1) refetchRatings(ratingsPage);
  }, [ratingsPage, refetchRatings]);

  const handleMessage = async () => {
    if (!userId) return;
    try {
      const room = await chatService.createRoom(userId);
      navigate(`/chats/${room.id}`);
    } catch {
      navigate('/chats');
    }
  };

  const handleReviewSubmit = async (score: number, comment: string) => {
    if (!userId) return;
    await userService.postRating(userId, score, comment || undefined);
    refetchRatings();
  };

  if (loading) return <Loader fullPage />;
  if (error || !user) {
    return <ErrorState message={error || undefined} onRetry={refetchUser} />;
  }

  // Redirect to own profile if viewing self
  if (currentUser && currentUser.id === userId) {
    navigate('/profile', { replace: true });
    return null;
  }

  return (
    <div className={styles.page}>
      <ProfileHeader
        user={user}
        onMessage={handleMessage}
      />

      <ProfileTabs
        listings={listings}
        listingsMeta={listingsMeta}
        onListingsPageChange={setListingsPage}
        listingsLoading={listingsLoading}
        listingsError={listingsError}
        onRetryListings={fetchListings}
        ratings={ratings}
        ratingsMeta={ratingsMeta}
        onRatingsPageChange={setRatingsPage}
        ratingsLoading={ratingsLoading}
        onRetryRatings={() => refetchRatings(ratingsPage)}
        reviewForm={<ReviewForm onSubmit={handleReviewSubmit} />}
      />
    </div>
  );
}
