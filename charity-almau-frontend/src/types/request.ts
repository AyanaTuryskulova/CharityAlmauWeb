export type RequestStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "CANCELLED";

export interface Request {
  id: string;
  message: string | null;
  status: RequestStatus;
  listingId: string;
  senderId: string;
  receiverId: string;
  createdAt: string;
  updatedAt: string;
  listing: { id: string; title: string; images: string[] };
  sender: { id: string; name: string; avatarUrl: string | null; rating: number };
  receiver: { id: string; name: string; avatarUrl: string | null; rating: number };
}
