export interface ChatRoom {
  id: string;
  listingId: string | null;
  createdAt: string;
  updatedAt: string;
  otherUser: { id: string; name: string; avatarUrl: string | null; rating: number };
  listing: { id: string; title: string; images: string[] } | null;
  lastMessage: { id: string; text: string; senderId: string; createdAt: string; isRead: boolean } | null;
  unreadCount: number;
}

export interface Message {
  id: string;
  text: string;
  isRead: boolean;
  senderId: string;
  chatRoomId: string;
  createdAt: string;
}
