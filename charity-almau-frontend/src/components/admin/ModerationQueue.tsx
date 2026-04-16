import type { Listing } from '../../types/listing';
import ModerationCard from './ModerationCard';
import styles from './ModerationQueue.module.css';

interface ModerationQueueProps {
  listings: Listing[];
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
}

export default function ModerationQueue({ listings, onApprove, onReject }: ModerationQueueProps) {
  return (
    <div className={styles.queue}>
      {listings.map((listing) => (
        <ModerationCard
          key={listing.id}
          listing={listing}
          onApprove={onApprove}
          onReject={onReject}
        />
      ))}
    </div>
  );
}
