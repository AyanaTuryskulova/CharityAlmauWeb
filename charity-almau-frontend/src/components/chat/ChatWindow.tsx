import { useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useChat } from '../../contexts/ChatContext';
import { useMessages } from '../../hooks/useMessages';
import { getImageUrl } from '../../constants';
import Avatar from '../common/Avatar';
import Loader from '../common/Loader';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import TypingIndicator from './TypingIndicator';
import type { ChatRoom } from '../../types/chat';
import styles from './ChatWindow.module.css';

interface ChatWindowProps {
  room: ChatRoom;
  onBack?: () => void;
}

export default function ChatWindow({ room, onBack }: ChatWindowProps) {
  const { t } = useTranslation('chat');
  const { user } = useAuth();
  const { sendMessage, startTyping, stopTyping, typingUsers } = useChat();
  const { messages, isLoading, hasMore, loadMore } = useMessages(room.id);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevMessagesLenRef = useRef(0);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > prevMessagesLenRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevMessagesLenRef.current = messages.length;
  }, [messages.length]);

  // Scroll on initial load
  useEffect(() => {
    if (!isLoading && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView();
    }
  }, [isLoading, room.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (el && el.scrollTop === 0 && hasMore && !isLoading) {
      loadMore();
    }
  }, [hasMore, isLoading, loadMore]);

  const handleSend = useCallback((text: string) => {
    sendMessage(room.id, text);
  }, [sendMessage, room.id]);

  const handleTyping = useCallback(() => {
    startTyping(room.id);
  }, [startTyping, room.id]);

  const handleStopTyping = useCallback(() => {
    stopTyping(room.id);
  }, [stopTyping, room.id]);

  const roomTypingUsers = typingUsers[room.id] || [];
  const isOtherTyping = roomTypingUsers.length > 0 && !roomTypingUsers.includes(user?.id || '');

  return (
    <div className={styles.window}>
      {/* Header */}
      <div className={styles.header}>
        {onBack && (
          <button className={styles.backBtn} onClick={onBack}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M13 4L7 10L13 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        )}
        <Link to={`/users/${room.otherUser.id}`} className={styles.userInfo}>
          <Avatar src={room.otherUser.avatarUrl} name={room.otherUser.name} size={36} />
          <div>
            <div className={styles.userName}>{room.otherUser.name}</div>
          </div>
        </Link>
        {room.listing && (
          <Link to={`/listings/${room.listing.id}`} className={styles.linkedListing}>
            {room.listing.images[0] && (
              <img src={getImageUrl(room.listing.images[0])} alt="" className={styles.listingImg} />
            )}
            <span className={styles.listingTitle}>{room.listing.title}</span>
          </Link>
        )}
      </div>

      {/* Messages */}
      <div className={styles.messages} ref={containerRef} onScroll={handleScroll}>
        {isLoading && messages.length === 0 && (
          <div className={styles.loaderWrap}>
            <Loader />
          </div>
        )}
        {hasMore && messages.length > 0 && (
          <div className={styles.loadMore}>
            {isLoading ? <Loader size="sm" /> : (
              <button className={styles.loadMoreBtn} onClick={loadMore}>...</button>
            )}
          </div>
        )}
        {!isLoading && messages.length === 0 && (
          <div className={styles.emptyMessages}>{t('noMessages')}</div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isOwn={msg.senderId === user?.id}
          />
        ))}
        {isOtherTyping && (
          <TypingIndicator name={room.otherUser.name} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSend}
        onTyping={handleTyping}
        onStopTyping={handleStopTyping}
      />
    </div>
  );
}
