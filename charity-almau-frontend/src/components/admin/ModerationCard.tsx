import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Listing } from '../../types/listing';
import { getImageUrl } from '../../constants';
import Avatar from '../common/Avatar';
import Badge from '../common/Badge';
import Button from '../common/Button';
import Modal from '../common/Modal';
import styles from './ModerationCard.module.css';

interface ModerationCardProps {
  listing: Listing;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
}

export default function ModerationCard({ listing, onApprove, onReject }: ModerationCardProps) {
  const { t } = useTranslation(['admin', 'listings']);
  const [loading, setLoading] = useState<'approve' | 'reject' | null>(null);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const imageUrl = listing.images[0] ? getImageUrl(listing.images[0]) : null;

  const handleApprove = async () => {
    setLoading('approve');
    try {
      await onApprove(listing.id);
    } finally {
      setLoading(null);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    setLoading('reject');
    try {
      await onReject(listing.id, rejectReason.trim());
      setRejectModalOpen(false);
      setRejectReason('');
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <div className={styles.card}>
        <Link to={`/listings/${listing.id}`} className={styles.imageLink}>
          {imageUrl ? (
            <img src={imageUrl} alt={listing.title} className={styles.image} />
          ) : (
            <div className={styles.imagePlaceholder} />
          )}
        </Link>

        <div className={styles.content}>
          <div className={styles.top}>
            <Link to={`/listings/${listing.id}`} className={styles.title}>
              {listing.title}
            </Link>
            <Badge variant={listing.type === 'FREE' ? 'accent' : 'primary'}>
              {t(`listings:types.${listing.type}`)}
            </Badge>
          </div>

          <p className={styles.description}>{listing.description}</p>

          <div className={styles.meta}>
            <span className={styles.category}>{t(`listings:categories.${listing.category}`)}</span>
            <span className={styles.date}>
              {new Date(listing.createdAt).toLocaleDateString()}
            </span>
          </div>

          <div className={styles.user}>
            <Avatar src={listing.user.avatarUrl} name={listing.user.name} size={24} />
            <Link to={`/users/${listing.userId}`} className={styles.userName}>
              {listing.user.name}
            </Link>
          </div>

          <div className={styles.actions}>
            <Button
              variant="primary"
              size="sm"
              loading={loading === 'approve'}
              disabled={loading !== null}
              onClick={handleApprove}
            >
              {t('admin:approve')}
            </Button>
            <Button
              variant="danger"
              size="sm"
              disabled={loading !== null}
              onClick={() => setRejectModalOpen(true)}
            >
              {t('admin:reject')}
            </Button>
          </div>
        </div>
      </div>

      <Modal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title={t('admin:rejectReason')}
      >
        <div className={styles.rejectForm}>
          <textarea
            className={styles.rejectInput}
            placeholder={t('admin:rejectPlaceholder')}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4}
          />
          <div className={styles.rejectActions}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRejectModalOpen(false)}
            >
              {t('common:cancel')}
            </Button>
            <Button
              variant="danger"
              size="sm"
              loading={loading === 'reject'}
              disabled={!rejectReason.trim()}
              onClick={handleReject}
            >
              {t('admin:reject')}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
