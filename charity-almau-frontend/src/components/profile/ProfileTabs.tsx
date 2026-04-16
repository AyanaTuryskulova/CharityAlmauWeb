import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../../types/listing';
import type { Rating } from '../../types/rating';
import ListingGrid from '../listings/ListingGrid';
import ReviewCard from './ReviewCard';
import EmptyState from '../common/EmptyState';
import ErrorState from '../common/ErrorState';
import Pagination from '../common/Pagination';
import Loader from '../common/Loader';
import styles from './ProfileTabs.module.css';

interface ProfileTabsProps {
  listings: Listing[];
  listingsMeta?: { page: number; totalPages: number } | null;
  onListingsPageChange?: (page: number) => void;
  listingsLoading?: boolean;
  listingsError?: string | null;
  onRetryListings?: () => void;
  favorites?: Listing[];
  favoritesMeta?: { page: number; totalPages: number } | null;
  onFavoritesPageChange?: (page: number) => void;
  favoritesLoading?: boolean;
  favoritesError?: string | null;
  onRetryFavorites?: () => void;
  ratings: Rating[];
  ratingsMeta?: { page: number; totalPages: number } | null;
  onRatingsPageChange?: (page: number) => void;
  ratingsLoading?: boolean;
  ratingsError?: string | null;
  onRetryRatings?: () => void;
  showFavorites?: boolean;
  onFavoriteToggle?: (id: string, isFavorited: boolean) => void;
  reviewForm?: React.ReactNode;
}

type Tab = 'listings' | 'favorites' | 'reviews';

export default function ProfileTabs({
  listings,
  listingsMeta,
  onListingsPageChange,
  listingsLoading,
  listingsError,
  onRetryListings,
  favorites,
  favoritesMeta,
  onFavoritesPageChange,
  favoritesLoading,
  favoritesError,
  onRetryFavorites,
  ratings,
  ratingsMeta,
  onRatingsPageChange,
  ratingsLoading,
  ratingsError,
  onRetryRatings,
  showFavorites,
  onFavoriteToggle,
  reviewForm,
}: ProfileTabsProps) {
  const { t } = useTranslation('profile');
  const [activeTab, setActiveTab] = useState<Tab>('listings');

  const tabs: Tab[] = showFavorites ? ['listings', 'favorites', 'reviews'] : ['listings', 'reviews'];

  return (
    <div className={styles.wrapper}>
      <div className={styles.tabs}>
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`${styles.tab} ${activeTab === tab ? styles.active : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {t(tab)}
          </button>
        ))}
      </div>

      <div className={styles.content}>
        {activeTab === 'listings' && (
          <>
            {listingsLoading ? (
              <Loader />
            ) : listingsError ? (
              <ErrorState message={listingsError} onRetry={onRetryListings} />
            ) : listings.length > 0 ? (
              <>
                <ListingGrid listings={listings} onFavoriteToggle={onFavoriteToggle} />
                {listingsMeta && onListingsPageChange && listingsMeta.totalPages > 1 && (
                  <Pagination
                    page={listingsMeta.page}
                    totalPages={listingsMeta.totalPages}
                    onPageChange={onListingsPageChange}
                  />
                )}
              </>
            ) : (
              <EmptyState icon="📋" title={t('noListings')} description={t('noListingsDesc')} />
            )}
          </>
        )}

        {activeTab === 'favorites' && showFavorites && (
          <>
            {favoritesLoading ? (
              <Loader />
            ) : favoritesError ? (
              <ErrorState message={favoritesError} onRetry={onRetryFavorites} />
            ) : favorites && favorites.length > 0 ? (
              <>
                <ListingGrid listings={favorites} onFavoriteToggle={onFavoriteToggle} />
                {favoritesMeta && onFavoritesPageChange && favoritesMeta.totalPages > 1 && (
                  <Pagination
                    page={favoritesMeta.page}
                    totalPages={favoritesMeta.totalPages}
                    onPageChange={onFavoritesPageChange}
                  />
                )}
              </>
            ) : (
              <EmptyState icon="❤️" title={t('noFavorites')} description={t('noFavoritesDesc')} />
            )}
          </>
        )}

        {activeTab === 'reviews' && (
          <>
            {reviewForm}
            {ratingsLoading ? (
              <Loader />
            ) : ratingsError ? (
              <ErrorState message={ratingsError} onRetry={onRetryRatings} />
            ) : ratings.length > 0 ? (
              <div className={styles.reviewsList}>
                {ratings.map((rating) => (
                  <ReviewCard key={rating.id} rating={rating} />
                ))}
                {ratingsMeta && onRatingsPageChange && ratingsMeta.totalPages > 1 && (
                  <Pagination
                    page={ratingsMeta.page}
                    totalPages={ratingsMeta.totalPages}
                    onPageChange={onRatingsPageChange}
                  />
                )}
              </div>
            ) : (
              <EmptyState icon="⭐" title={t('noReviews')} description={t('noReviewsDesc')} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
