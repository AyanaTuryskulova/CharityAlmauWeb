import type { Request } from '../../types/request';
import RequestCard from './RequestCard';
import styles from './RequestList.module.css';

interface RequestListProps {
  requests: Request[];
  type: 'incoming' | 'outgoing';
  onAccept?: (id: string) => Promise<void>;
  onReject?: (id: string) => Promise<void>;
  onCancel?: (id: string) => Promise<void>;
}

export default function RequestList({ requests, type, onAccept, onReject, onCancel }: RequestListProps) {
  return (
    <div className={styles.list}>
      {requests.map((req) => (
        <RequestCard
          key={req.id}
          request={req}
          type={type}
          onAccept={onAccept}
          onReject={onReject}
          onCancel={onCancel}
        />
      ))}
    </div>
  );
}
