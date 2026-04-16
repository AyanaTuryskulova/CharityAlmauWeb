import type { Message } from '../../types/chat';
import styles from './MessageBubble.module.css';

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  return (
    <div className={`${styles.wrapper} ${isOwn ? styles.own : styles.other}`}>
      <div className={`${styles.bubble} ${isOwn ? styles.bubbleOwn : styles.bubbleOther}`}>
        <p className={styles.text}>{message.text}</p>
        <span className={styles.time}>
          {formatTime(message.createdAt)}
          {isOwn && (
            <span className={styles.status}>
              {message.isRead ? ' \u2713\u2713' : ' \u2713'}
            </span>
          )}
        </span>
      </div>
    </div>
  );
}
