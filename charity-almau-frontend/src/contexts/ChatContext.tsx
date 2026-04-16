import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import type { ChatRoom, Message } from '../types/chat';
import { chatService } from '../services/chatService';
import { socketService } from '../services/socketService';
import { useAuth } from './AuthContext';

interface ChatContextValue {
  rooms: ChatRoom[];
  isLoadingRooms: boolean;
  roomsError: string | null;
  totalUnread: number;
  typingUsers: Record<string, string[]>; // roomId → userIds
  sendMessage: (roomId: string, text: string) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  startTyping: (roomId: string) => void;
  stopTyping: (roomId: string) => void;
  markRead: (roomId: string) => void;
  refreshRooms: () => Promise<void>;
  onNewMessage: (callback: (msg: Message) => void) => () => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { token, user } = useAuth();
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [isLoadingRooms, setIsLoadingRooms] = useState(false);
  const [roomsError, setRoomsError] = useState<string | null>(null);
  const [typingUsers, setTypingUsers] = useState<Record<string, string[]>>({});
  const messageListenersRef = useRef<Set<(msg: Message) => void>>(new Set());

  const totalUnread = rooms.reduce((sum, r) => sum + r.unreadCount, 0);

  const refreshRooms = useCallback(async () => {
    setIsLoadingRooms(true);
    setRoomsError(null);
    try {
      const data = await chatService.getRooms();
      setRooms(data);
    } catch (err: unknown) {
      setRoomsError(err instanceof Error ? err.message : 'Failed to load chats');
    } finally {
      setIsLoadingRooms(false);
    }
  }, []);

  // Connect socket and fetch rooms when token is available
  useEffect(() => {
    if (!token) return;

    socketService.connect(token);
    refreshRooms();

    const offMessage = socketService.onMessage((msg: Message) => {
      // Update rooms list
      setRooms((prev) =>
        prev.map((room) => {
          if (room.id !== msg.chatRoomId) return room;
          return {
            ...room,
            lastMessage: {
              id: msg.id,
              text: msg.text,
              senderId: msg.senderId,
              createdAt: msg.createdAt,
              isRead: msg.isRead,
            },
            unreadCount: msg.senderId !== user?.id ? room.unreadCount + 1 : room.unreadCount,
            updatedAt: msg.createdAt,
          };
        })
      );

      // Notify listeners
      messageListenersRef.current.forEach((cb) => cb(msg));
    });

    const offTyping = socketService.onTyping(({ roomId, userId }) => {
      setTypingUsers((prev) => {
        const current = prev[roomId] || [];
        if (current.includes(userId)) return prev;
        return { ...prev, [roomId]: [...current, userId] };
      });
    });

    const offStopTyping = socketService.onStopTyping(({ roomId, userId }) => {
      setTypingUsers((prev) => {
        const current = prev[roomId] || [];
        return { ...prev, [roomId]: current.filter((id) => id !== userId) };
      });
    });

    const offRead = socketService.onRead(({ roomId }) => {
      setRooms((prev) =>
        prev.map((room) => (room.id === roomId ? { ...room, unreadCount: 0 } : room))
      );
    });

    return () => {
      offMessage?.();
      offTyping?.();
      offStopTyping?.();
      offRead?.();
      socketService.disconnect();
    };
  }, [token, user?.id, refreshRooms]);

  const sendMessage = useCallback((roomId: string, text: string) => {
    socketService.sendMessage(roomId, text);
  }, []);

  const joinRoom = useCallback((roomId: string) => {
    socketService.joinRoom(roomId);
  }, []);

  const leaveRoom = useCallback((roomId: string) => {
    socketService.leaveRoom(roomId);
  }, []);

  const startTyping = useCallback((roomId: string) => {
    socketService.startTyping(roomId);
  }, []);

  const stopTyping = useCallback((roomId: string) => {
    socketService.stopTyping(roomId);
  }, []);

  const markRead = useCallback((roomId: string) => {
    socketService.markRead(roomId);
    chatService.markRead(roomId);
    setRooms((prev) =>
      prev.map((room) => (room.id === roomId ? { ...room, unreadCount: 0 } : room))
    );
  }, []);

  const onNewMessage = useCallback((callback: (msg: Message) => void) => {
    messageListenersRef.current.add(callback);
    return () => { messageListenersRef.current.delete(callback); };
  }, []);

  return (
    <ChatContext.Provider
      value={{
        rooms,
        isLoadingRooms,
        roomsError,
        totalUnread,
        typingUsers,
        sendMessage,
        joinRoom,
        leaveRoom,
        startTyping,
        stopTyping,
        markRead,
        refreshRooms,
        onNewMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}
