import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useListing } from '../hooks/useListing';
import { listingsService } from '../services/listingsService';
import { useNotification } from '../contexts/NotificationContext';
import ListingForm from '../components/listings/ListingForm';
import Loader from '../components/common/Loader';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import styles from './EditListingPage.module.css';

export default function EditListingPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation('listings');
  const { t: tc } = useTranslation();
  const navigate = useNavigate();
  const { showToast } = useNotification();
  const { listing, loading: fetchLoading, error } = useListing(id);
  const [submitting, setSubmitting] = useState(false);

  if (fetchLoading) return <Loader fullPage />;
  if (error || !listing) {
    return (
      <EmptyState
        icon="📦"
        title={t('detail.notFound')}
        description={t('detail.notFoundDesc')}
        action={<Button onClick={() => navigate('/my-listings')}>{tc('back')}</Button>}
      />
    );
  }

  const handleSubmit = async (formData: FormData) => {
    setSubmitting(true);
    try {
      await listingsService.updateListing(listing.id, formData);
      showToast(t('create.saveChanges'), 'success');
      navigate(`/listings/${listing.id}`);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : tc('error'), 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t('create.editTitle')}</h1>
      <ListingForm initialData={listing} onSubmit={handleSubmit} loading={submitting} />
    </div>
  );
}
