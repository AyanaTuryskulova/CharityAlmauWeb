import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Avatar from '../common/Avatar';
import StarRating from '../common/StarRating';
import styles from './SellerCard.module.css';

interface SellerCardProps {
  user: {
    id: string;
    name: string;
    avatarUrl: string | null;
    rating: number;
  };
}

export default function SellerCard({ user }: SellerCardProps) {
  const { t } = useTranslation('listings');

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <Avatar src={user.avatarUrl} name={user.name} size={48} />
        <div className={styles.info}>
          <Link to={`/users/${user.id}`} className={styles.name}>
            {user.name}
          </Link>
          <StarRating value={user.rating} readonly size="sm" />
        </div>
      </div>
      <Link to={`/users/${user.id}`} className={styles.allLink}>
        {t('detail.allListings')}
      </Link>
    </div>
  );
}
