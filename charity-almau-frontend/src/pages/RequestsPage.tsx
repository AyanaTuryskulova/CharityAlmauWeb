import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRequests } from '../hooks/useRequests';
import RequestList from '../components/requests/RequestList';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Pagination from '../components/common/Pagination';
import styles from './RequestsPage.module.css';

type Tab = 'incoming' | 'outgoing';

export default function RequestsPage() {
  const { t } = useTranslation('requests');
  const [tab, setTab] = useState<Tab>('incoming');
  const [page, setPage] = useState(1);

  const {
    requests,
    meta,
    loading,
    error,
    refetch,
    acceptRequest,
    rejectRequest,
    cancelRequest,
  } = useRequests(tab, { page, limit: 20 });

  const handleTabChange = (newTab: Tab) => {
    setTab(newTab);
    setPage(1);
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t('title')}</h1>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === 'incoming' ? styles.tabActive : ''}`}
          onClick={() => handleTabChange('incoming')}
        >
          {t('incoming')}
        </button>
        <button
          className={`${styles.tab} ${tab === 'outgoing' ? styles.tabActive : ''}`}
          onClick={() => handleTabChange('outgoing')}
        >
          {t('outgoing')}
        </button>
      </div>

      {loading ? (
        <Loader fullPage />
      ) : error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : requests.length === 0 ? (
        <EmptyState
          icon="📨"
          title={t('empty')}
          description={tab === 'incoming' ? t('emptyIncomingDesc') : t('emptyOutgoingDesc')}
        />
      ) : (
        <>
          <RequestList
            requests={requests}
            type={tab}
            onAccept={acceptRequest}
            onReject={rejectRequest}
            onCancel={cancelRequest}
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
