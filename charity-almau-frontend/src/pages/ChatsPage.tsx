import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useChats } from '../hooks/useChats';
import ChatSidebar from '../components/chat/ChatSidebar';
import ChatWindow from '../components/chat/ChatWindow';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import styles from './ChatsPage.module.css';

export default function ChatsPage() {
  const { chatId } = useParams<{ chatId?: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('chat');
  const { rooms, isLoading, error, refreshRooms } = useChats();
  const [mobileView, setMobileView] = useState<'sidebar' | 'chat'>(chatId ? 'chat' : 'sidebar');

  const activeRoom = chatId ? rooms.find((r) => r.id === chatId) ?? null : null;

  useEffect(() => {
    const view = chatId ? 'chat' : 'sidebar';
    Promise.resolve().then(() => setMobileView(view));
  }, [chatId]);

  const handleSelectChat = useCallback((roomId: string) => {
    navigate(`/chats/${roomId}`);
  }, [navigate]);

  const handleBack = useCallback(() => {
    navigate('/chats');
  }, [navigate]);

  if (isLoading) {
    return <Loader fullPage />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={refreshRooms} />;
  }

  return (
    <div className={styles.page}>
      <div className={`${styles.sidebar} ${mobileView === 'chat' ? styles.hideMobile : ''}`}>
        <ChatSidebar
          rooms={rooms}
          activeChatId={chatId ?? null}
          onSelectChat={handleSelectChat}
        />
      </div>
      <div className={`${styles.main} ${mobileView === 'sidebar' ? styles.hideMobile : ''}`}>
        {activeRoom ? (
          <ChatWindow room={activeRoom} onBack={handleBack} />
        ) : (
          <div className={styles.placeholder}>
            <EmptyState
              icon="💬"
              title={rooms.length === 0 ? t('empty') : t('selectChat')}
              description={rooms.length === 0 ? t('emptyDesc') : t('selectChatDesc')}
            />
          </div>
        )}
      </div>
    </div>
  );
}
