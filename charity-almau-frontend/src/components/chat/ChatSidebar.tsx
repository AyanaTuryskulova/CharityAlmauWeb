import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { getImageUrl } from '../../constants';
import Avatar from '../common/Avatar';
import styles from './ChatSidebar.module.css';
import type { ChatRoom } from '../../types/chat';

interface ChatSidebarProps {
  rooms: ChatRoom[];
  activeChatId: string | null;
  onSelectChat: (roomId: string) => void;
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (diffDays === 1) return 'Вчера';
  if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  }
  return date.toLocaleDateString([], { day: 'numeric', month: 'short' });
}

export default function ChatSidebar({ rooms, activeChatId, onSelectChat }: ChatSidebarProps) {
  const { t } = useTranslation('chat');
  const { user } = useAuth();

  if (rooms.length === 0) {
    return (
      <div className={styles.sidebar}>
        <div className={styles.header}>
          <h2 className={styles.title}>{t('title')}</h2>
        </div>
        <div className={styles.empty}>{t('empty')}</div>
      </div>
    );
  }

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <h2 className={styles.title}>{t('title')}</h2>
      </div>
      <div className={styles.list}>
        {rooms.map((room) => {
          const isActive = room.id === activeChatId;
          const lastMsg = room.lastMessage;
          const isOwnMsg = lastMsg?.senderId === user?.id;

          return (
            <button
              key={room.id}
              className={`${styles.item} ${isActive ? styles.active : ''}`}
              onClick={() => onSelectChat(room.id)}
            >
              <Avatar
                src={room.otherUser.avatarUrl}
                name={room.otherUser.name}
                size={48}
              />
              <div className={styles.content}>
                <div className={styles.top}>
                  <span className={styles.name}>{room.otherUser.name}</span>
                  {lastMsg && (
                    <span className={styles.time}>{formatTime(lastMsg.createdAt)}</span>
                  )}
                </div>
                <div className={styles.bottom}>
                  <span className={styles.lastMsg}>
                    {lastMsg
                      ? `${isOwnMsg ? 'Вы: ' : ''}${lastMsg.text}`
                      : t('noMessages')}
                  </span>
                  {room.unreadCount > 0 && (
                    <span className={styles.badge}>{room.unreadCount}</span>
                  )}
                </div>
                {room.listing && (
                  <div className={styles.listing}>
                    {room.listing.images[0] && (
                      <img
                        src={getImageUrl(room.listing.images[0])}
                        alt=""
                        className={styles.listingImg}
                      />
                    )}
                    <span className={styles.listingTitle}>{room.listing.title}</span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
