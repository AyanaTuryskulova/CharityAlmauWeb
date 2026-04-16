export interface Rating {
  id: string;
  score: number;
  comment: string | null;
  authorId: string;
  listingId: string | null;
  createdAt: string;
  author: { id: string; name: string; avatarUrl: string | null };
}
