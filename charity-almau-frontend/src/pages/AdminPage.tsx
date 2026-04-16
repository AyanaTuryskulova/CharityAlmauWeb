import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { adminService, type AdminStats } from '../services/adminService';
import type { Listing } from '../types/listing';
import { useNotification } from '../contexts/NotificationContext';
import ModerationQueue from '../components/admin/ModerationQueue';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import styles from './AdminPage.module.css';

export default function AdminPage() {
  const { t } = useTranslation('admin');
  const { t: tc } = useTranslation();
  const { showToast } = useNotification();

  const [listings, setListings] = useState<Listing[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [listingsRes, statsRes] = await Promise.all([
        adminService.getPendingListings({ page, limit: 10 }),
        adminService.getStats(),
      ]);
      setListings(listingsRes.data);
      setTotalPages(listingsRes.meta.totalPages);
      setStats(statsRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : tc('error');
      setError(msg);
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [page, showToast, tc]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApprove = async (id: string) => {
    try {
      await adminService.approveListing(id);
      setListings((prev) => prev.filter((l) => l.id !== id));
      if (stats) setStats({ ...stats, pendingListings: stats.pendingListings - 1 });
      showToast(t('approve'), 'success');
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : tc('error'), 'error');
    }
  };

  const handleReject = async (id: string, reason: string) => {
    try {
      await adminService.rejectListing(id, reason);
      setListings((prev) => prev.filter((l) => l.id !== id));
      if (stats) setStats({ ...stats, pendingListings: stats.pendingListings - 1 });
      showToast(t('reject'), 'success');
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : tc('error'), 'error');
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t('title')}</h1>

      {stats && (
        <div className={styles.stats}>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.totalUsers}</span>
            <span className={styles.statLabel}>{t('stats.users')}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.totalListings}</span>
            <span className={styles.statLabel}>{t('stats.listings')}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{stats.pendingListings}</span>
            <span className={styles.statLabel}>{t('stats.pending')}</span>
          </div>
        </div>
      )}

      <h2 className={styles.sectionTitle}>{t('moderation')}</h2>

      {loading ? (
        <Loader fullPage />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : listings.length === 0 ? (
        <EmptyState icon="✅" title={t('empty')} description={t('emptyDesc')} />
      ) : (
        <>
          <ModerationQueue
            listings={listings}
            onApprove={handleApprove}
            onReject={handleReject}
          />
          <div className={styles.pagination}>
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
