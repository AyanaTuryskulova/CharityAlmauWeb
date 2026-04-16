import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../../types/listing';
import { getImageUrl } from '../../constants';
import Avatar from '../common/Avatar';
import styles from './ListingCard.module.css';

interface ListingCardProps {
  listing: Listing;
  onFavoriteToggle?: (id: string, isFavorited: boolean) => void;
  showStatus?: boolean;
  showActions?: boolean;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export default function ListingCard({
  listing,
  onFavoriteToggle,
  showStatus,
  showActions,
  onEdit,
  onDelete,
}: ListingCardProps) {
  const { t } = useTranslation('listings');

  const imageUrl = listing.images[0] ? getImageUrl(listing.images[0]) : null;

  const typeLabel = t(`types.${listing.type}`);
  const isAccent = listing.type === 'FREE';

  const priceDisplay = () => {
    if (listing.type === 'RENT' && listing.rentalPrice != null) {
      return `${listing.rentalPrice} ₸/${t('detail.perDay')}`;
    }
    if (listing.type === 'EXCHANGE') return typeLabel;
    return typeLabel;
  };

  return (
    <div className={styles.card}>
      <Link to={`/listings/${listing.id}`} className={styles.imageLink}>
        <div className={styles.imageWrap}>
          {imageUrl ? (
            <img src={imageUrl} alt={listing.title} className={styles.image} />
          ) : (
            <div className={styles.placeholder} />
          )}
          {onFavoriteToggle && (
            <button
              className={`${styles.heartBtn} ${listing.isFavorited ? styles.hearted : ''}`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onFavoriteToggle(listing.id, listing.isFavorited);
              }}
            >
              {listing.isFavorited ? '\u2764' : '\u2661'}
            </button>
          )}
        </div>
      </Link>

      <div className={styles.info}>
        <div className={styles.titleRow}>
          <Link to={`/listings/${listing.id}`} className={styles.title}>
            {listing.title}
          </Link>
          <span className={`${styles.price} ${isAccent ? styles.priceAccent : styles.pricePrimary}`}>
            {priceDisplay()}
          </span>
        </div>

        {showStatus && (
          <span className={`${styles.statusBadge} ${styles[`status_${listing.status}`]}`}>
            {t(`statuses.${listing.status}`)}
          </span>
        )}

        <div className={styles.meta}>
          <div className={styles.author}>
            <Avatar src={listing.user.avatarUrl} name={listing.user.name} size={20} />
            <span className={styles.authorName}>{listing.user.name}</span>
          </div>
          <span className={styles.category}>{t(`categories.${listing.category}`)}</span>
        </div>

        {showActions && (
          <div className={styles.actions}>
            {onEdit && (
              <button className={styles.editBtn} onClick={() => onEdit(listing.id)}>
                {t('create.editTitle', { defaultValue: 'Edit' })}
              </button>
            )}
            {onDelete && (
              <button className={styles.deleteBtn} onClick={() => onDelete(listing.id)}>
                {t('common:delete', { defaultValue: 'Delete' })}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
