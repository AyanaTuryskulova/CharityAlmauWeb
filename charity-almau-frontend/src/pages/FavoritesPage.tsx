import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useFavorites } from '../hooks/useFavorites';
import ListingGrid from '../components/listings/ListingGrid';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Pagination from '../components/common/Pagination';
import Button from '../components/common/Button';
import styles from './FavoritesPage.module.css';

export default function FavoritesPage() {
  const { t } = useTranslation('listings');
  const [page, setPage] = useState(1);

  const { favorites, meta, loading, error, toggleFavorite, refetch } = useFavorites({
    page,
    limit: 20,
  });

  const handleFavoriteToggle = async (id: string, isFavorited: boolean) => {
    await toggleFavorite(id, isFavorited);
    refetch();
  };

  if (loading && page === 1) return <Loader fullPage />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('favorites.title')}</h1>
        {meta && meta.total > 0 && (
          <span className={styles.count}>{meta.total}</span>
        )}
      </div>

      {loading && page > 1 ? (
        <Loader fullPage />
      ) : error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : favorites.length === 0 ? (
        <EmptyState
          icon="❤️"
          title={t('favorites.empty')}
          description={t('favorites.emptyDesc')}
          action={
            <Link to="/">
              <Button variant="primary">{t('favorites.browseCatalog')}</Button>
            </Link>
          }
        />
      ) : (
        <>
          <ListingGrid
            listings={favorites}
            onFavoriteToggle={handleFavoriteToggle}
          />

          {meta && meta.totalPages > 1 && (
            <div className={styles.pagination}>
              <Pagination
                page={page}
                totalPages={meta.totalPages}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
