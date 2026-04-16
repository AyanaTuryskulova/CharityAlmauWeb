import { useState, useEffect, useCallback, useRef } from 'react';
import type { Message } from '../types/chat';
import { chatService } from '../services/chatService';
import { useChat } from '../contexts/ChatContext';

export function useMessages(roomId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const pageRef = useRef(1);
  const { joinRoom, leaveRoom, markRead, onNewMessage } = useChat();

  const fetchMessages = useCallback(async (page: number) => {
    if (!roomId) return;
    setIsLoading(true);
    try {
      const res = await chatService.getMessages(roomId, { page, limit: 30 });
      if (page === 1) {
        setMessages(res.data.reverse());
      } else {
        setMessages((prev) => [...res.data.reverse(), ...prev]);
      }
      setHasMore(page < res.meta.totalPages);
      pageRef.current = page;
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  }, [roomId]);

  // Join room and load initial messages
  useEffect(() => {
    if (!roomId) {
      setMessages([]);
      setHasMore(true);
      pageRef.current = 1;
      return;
    }

    joinRoom(roomId);
    markRead(roomId);
    fetchMessages(1);

    return () => {
      leaveRoom(roomId);
    };
  }, [roomId, joinRoom, leaveRoom, markRead, fetchMessages]);

  // Listen for new messages in this room
  useEffect(() => {
    if (!roomId) return;

    const unsub = onNewMessage((msg: Message) => {
      if (msg.chatRoomId === roomId) {
        setMessages((prev) => [...prev, msg]);
        markRead(roomId);
      }
    });

    return unsub;
  }, [roomId, onNewMessage, markRead]);

  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      fetchMessages(pageRef.current + 1);
    }
  }, [isLoading, hasMore, fetchMessages]);

  return { messages, isLoading, hasMore, loadMore };
}
