import { useChat } from '../contexts/ChatContext';

export function useChats() {
  const { rooms, isLoadingRooms, roomsError, totalUnread, refreshRooms } = useChat();
  return { rooms, isLoading: isLoadingRooms, error: roomsError, totalUnread, refreshRooms };
}
