import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../../types/listing';
import { listingsService } from '../../services/listingsService';
import ListingCard from './ListingCard';
import Loader from '../common/Loader';
import styles from './SimilarItems.module.css';

interface SimilarItemsProps {
  listingId: string;
}

export default function SimilarItems({ listingId }: SimilarItemsProps) {
  const { t } = useTranslation('listings');
  const [items, setItems] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetchSimilar = async () => {
      setLoading(true);
      try {
        const res = await listingsService.getSimilar(listingId);
        if (!cancelled) setItems(res.data?.slice(0, 4) ?? []);
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchSimilar();
    return () => { cancelled = true; };
  }, [listingId]);

  if (!loading && items.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <h3 className={styles.title}>{t('detail.similar')}</h3>
      {loading ? (
        <div className={styles.loaderWrap}>
          <Loader />
        </div>
      ) : (
        <div className={styles.grid}>
          {items.map((item) => (
            <ListingCard key={item.id} listing={item} />
          ))}
        </div>
      )}
    </div>
  );
}
