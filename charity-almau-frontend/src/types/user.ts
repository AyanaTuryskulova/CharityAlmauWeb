export type UserRole = "USER" | "ADMIN";

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string | null;
  role: UserRole;
  rating: number;
  ratingCount: number;
  createdAt: string;
  _count?: {
    listings: number;
  };
}
