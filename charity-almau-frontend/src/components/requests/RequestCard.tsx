import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Request } from '../../types/request';
import { getImageUrl } from '../../constants';
import Avatar from '../common/Avatar';
import Badge from '../common/Badge';
import Button from '../common/Button';
import styles from './RequestCard.module.css';

type BadgeVariant = 'warning' | 'success' | 'neutral' | 'accent';

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  PENDING: 'warning',
  ACCEPTED: 'success',
  REJECTED: 'accent',
  CANCELLED: 'neutral',
};

interface RequestCardProps {
  request: Request;
  type: 'incoming' | 'outgoing';
  onAccept?: (id: string) => Promise<void>;
  onReject?: (id: string) => Promise<void>;
  onCancel?: (id: string) => Promise<void>;
}

export default function RequestCard({ request, type, onAccept, onReject, onCancel }: RequestCardProps) {
  const { t } = useTranslation('requests');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const imageUrl = request.listing.images[0] ? getImageUrl(request.listing.images[0]) : null;
  const otherUser = type === 'incoming' ? request.sender : request.receiver;
  const isPending = request.status === 'PENDING';

  const handleAction = async (action: string, fn?: (id: string) => Promise<void>) => {
    if (!fn) return;
    setActionLoading(action);
    try {
      await fn(request.id);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className={styles.card}>
      <Link to={`/listings/${request.listingId}`} className={styles.imageLink}>
        {imageUrl ? (
          <img src={imageUrl} alt={request.listing.title} className={styles.image} />
        ) : (
          <div className={styles.imagePlaceholder} />
        )}
      </Link>

      <div className={styles.content}>
        <div className={styles.top}>
          <Link to={`/listings/${request.listingId}`} className={styles.listingTitle}>
            {request.listing.title}
          </Link>
          <Badge variant={STATUS_VARIANT[request.status] || 'neutral'}>
            {t(`statuses.${request.status}`)}
          </Badge>
        </div>

        <div className={styles.user}>
          <Avatar src={otherUser.avatarUrl} name={otherUser.name} size={24} />
          <Link to={`/users/${otherUser.id}`} className={styles.userName}>
            {otherUser.name}
          </Link>
        </div>

        {request.message && (
          <p className={styles.message}>{request.message}</p>
        )}

        <div className={styles.date}>
          {new Date(request.createdAt).toLocaleDateString()}
        </div>

        {isPending && (
          <div className={styles.actions}>
            {type === 'incoming' && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  loading={actionLoading === 'accept'}
                  onClick={() => handleAction('accept', onAccept)}
                >
                  {t('accept')}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  loading={actionLoading === 'reject'}
                  onClick={() => handleAction('reject', onReject)}
                >
                  {t('reject')}
                </Button>
              </>
            )}
            {type === 'outgoing' && (
              <Button
                variant="ghost"
                size="sm"
                loading={actionLoading === 'cancel'}
                onClick={() => handleAction('cancel', onCancel)}
              >
                {t('cancel')}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
