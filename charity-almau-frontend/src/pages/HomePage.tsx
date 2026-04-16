import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useListings } from '../hooks/useListings';
import { useDebounce } from '../hooks/useDebounce';
import { favoritesService } from '../services/favoritesService';
import ListingGrid from '../components/listings/ListingGrid';
import ListingFilters from '../components/listings/ListingFilters';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Button from '../components/common/Button';
import styles from './HomePage.module.css';

export default function HomePage() {
  const { t } = useTranslation();
  const { t: tl } = useTranslation('listings');
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [typeFilter, setTypeFilter] = useState(searchParams.get('type') ?? '');
  const [categoryFilter, setCategoryFilter] = useState(searchParams.get('category') ?? '');
  const [search, setSearch] = useState(searchParams.get('search') ?? '');
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(search, 400);

  useEffect(() => {
    const searchValue = searchParams.get('search') ?? '';
    Promise.resolve().then(() => setSearch(searchValue));
  }, [searchParams]);

  const { listings, meta, loading, error, refetch } = useListings({
    page,
    limit: 20,
    type: typeFilter || undefined,
    category: categoryFilter || undefined,
    search: debouncedSearch || undefined,
    sort: 'createdAt:desc',
  });

  const handleFavoriteToggle = useCallback(async (id: string, isFavorited: boolean) => {
    try {
      if (isFavorited) {
        await favoritesService.removeFavorite(id);
      } else {
        await favoritesService.addFavorite(id);
      }
      refetch();
    } catch {
      // silently fail
    }
  }, [refetch]);

  const handleTypeChange = (type: string) => {
    setTypeFilter(type);
    setPage(1);
    const params = new URLSearchParams(searchParams);
    if (type) params.set('type', type);
    else params.delete('type');
    setSearchParams(params);
  };

  const handleCategoryChange = (category: string) => {
    setCategoryFilter(category);
    setPage(1);
    const params = new URLSearchParams(searchParams);
    if (category) params.set('category', category);
    else params.delete('category');
    setSearchParams(params);
  };

  const handleLoadMore = () => {
    setPage((p) => p + 1);
  };

  return (
    <div className={styles.page}>
      {user && (
        <div className={styles.greeting}>
          <h2 className={styles.greetText}>{tl('greeting', { name: user.name })}</h2>
          <p className={styles.greetSub}>{tl('newThisWeek', { count: meta?.total ?? 0 })}</p>
        </div>
      )}

      <div className={styles.toolbar}>
        <ListingFilters
          activeType={typeFilter}
          onTypeChange={handleTypeChange}
          activeCategory={categoryFilter}
          onCategoryChange={handleCategoryChange}
        />
      </div>

      {loading && page === 1 ? (
        <Loader fullPage />
      ) : error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : listings.length === 0 ? (
        <EmptyState icon="🔍" title={t('noResults')} description={t('noResultsDesc')} />
      ) : (
        <>
          <ListingGrid listings={listings} onFavoriteToggle={handleFavoriteToggle} />

          {meta && page < meta.totalPages && (
            <div className={styles.loadMore}>
              <Button variant="secondary" onClick={handleLoadMore} loading={loading}>
                {t('showMore')}
              </Button>
            </div>
          )}
        </>
      )}

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statNum}>340+</span>
          <span className={styles.statLabel}>{t('stats.students')}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statNum}>1200+</span>
          <span className={styles.statLabel}>{t('stats.listings')}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statNum}>{t('stats.commission')}</span>
        </div>
      </div>
    </div>
  );
}
