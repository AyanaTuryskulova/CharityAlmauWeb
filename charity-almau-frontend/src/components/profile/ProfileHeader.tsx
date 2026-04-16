import { useTranslation } from 'react-i18next';
import type { User } from '../../types/user';
import Avatar from '../common/Avatar';
import StarRating from '../common/StarRating';
import styles from './ProfileHeader.module.css';

interface ProfileHeaderProps {
  user: User;
  isOwn?: boolean;
  onEdit?: () => void;
  onMessage?: () => void;
}

export default function ProfileHeader({ user, isOwn, onEdit, onMessage }: ProfileHeaderProps) {
  const { t } = useTranslation('profile');

  const memberDate = new Date(user.createdAt).toLocaleDateString();

  return (
    <div className={styles.header}>
      <Avatar src={user.avatarUrl} name={user.name} size={96} className={styles.avatar} />

      <div className={styles.info}>
        <h1 className={styles.name}>{user.name}</h1>
        {isOwn && <p className={styles.email}>{user.email}</p>}

        <div className={styles.ratingRow}>
          <StarRating value={Math.round(user.rating ?? 0)} readonly size="sm" />
          <span className={styles.ratingText}>
            {(user.rating ?? 0).toFixed(1)} ({user.ratingCount ?? 0} {t('reviews').toLowerCase()})
          </span>
        </div>

        <div className={styles.stats}>
          {user._count?.listings != null && (
            <div className={styles.stat}>
              <span className={styles.statNum}>{user._count.listings}</span>
              <span className={styles.statLabel}>{t('listings')}</span>
            </div>
          )}
          <div className={styles.stat}>
            <span className={styles.statNum}>{user.ratingCount}</span>
            <span className={styles.statLabel}>{t('reviews')}</span>
          </div>
        </div>

        <p className={styles.memberSince}>
          {t('memberSince')} {memberDate}
        </p>
      </div>

      <div className={styles.actions}>
        {isOwn && onEdit && (
          <button className={styles.editBtn} onClick={onEdit}>
            {t('editProfile')}
          </button>
        )}
        {!isOwn && onMessage && (
          <button className={styles.messageBtn} onClick={onMessage}>
            {t('writeMessage')}
          </button>
        )}
      </div>
    </div>
  );
}
