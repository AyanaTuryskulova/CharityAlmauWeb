import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listingsService } from '../services/listingsService';
import { useNotification } from '../contexts/NotificationContext';
import ListingForm from '../components/listings/ListingForm';
import styles from './CreateListingPage.module.css';

export default function CreateListingPage() {
  const { t } = useTranslation('listings');
  const navigate = useNavigate();
  const { showToast } = useNotification();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (formData: FormData) => {
    setLoading(true);
    try {
      await listingsService.createListing(formData);
      showToast(t('create.title'), 'success');
      navigate('/my-listings');
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : t('common:error'), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t('create.title')}</h1>
      <ListingForm onSubmit={handleSubmit} loading={loading} />
    </div>
  );
}
