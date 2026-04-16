import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useListings } from '../hooks/useListings';
import { listingsService } from '../services/listingsService';
import { useNotification } from '../contexts/NotificationContext';
import ListingGrid from '../components/listings/ListingGrid';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Button from '../components/common/Button';
import styles from './MyListingsPage.module.css';

type StatusFilter = '' | 'PENDING' | 'APPROVED' | 'REJECTED';

const FILTERS: { key: StatusFilter; labelKey: string }[] = [
  { key: '', labelKey: 'my.filterAll' },
  { key: 'PENDING', labelKey: 'my.filterPending' },
  { key: 'APPROVED', labelKey: 'my.filterApproved' },
  { key: 'REJECTED', labelKey: 'my.filterRejected' },
];

export default function MyListingsPage() {
  const { t } = useTranslation('listings');
  const { t: tc } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useNotification();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('');

  const { listings, loading, error, refetch } = useListings({
    userId: user?.id,
    sort: 'createdAt:desc',
  });

  const filtered = statusFilter
    ? listings.filter((l) => l.status === statusFilter)
    : listings;

  const handleDelete = async (id: string) => {
    if (!window.confirm(tc('delete') + '?')) return;
    try {
      await listingsService.deleteListing(id);
      showToast(tc('delete'), 'success');
      refetch();
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : tc('error'), 'error');
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('my.title')}</h1>
        <Button variant="accent" onClick={() => navigate('/listings/new')}>
          {tc('nav.addListing')}
        </Button>
      </div>

      <div className={styles.filters}>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={`${styles.filterBtn} ${statusFilter === f.key ? styles.active : ''}`}
            onClick={() => setStatusFilter(f.key)}
          >
            {t(f.labelKey)}
          </button>
        ))}
      </div>

      {loading ? (
        <Loader fullPage />
      ) : error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="📋"
          title={t('my.empty')}
          description={t('my.emptyDesc')}
          action={
            <Button onClick={() => navigate('/listings/new')}>
              {tc('nav.addListing')}
            </Button>
          }
        />
      ) : (
        <ListingGrid
          listings={filtered}
          showStatus
          showActions
          onEdit={(id) => navigate(`/listings/${id}/edit`)}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}
