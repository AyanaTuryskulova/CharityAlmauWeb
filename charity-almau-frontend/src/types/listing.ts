export type ListingType = "FREE" | "EXCHANGE" | "RENT";
export type Category = "TEXTBOOKS" | "TECH" | "FURNITURE" | "CLOTHING" | "SPORTS" | "STATIONERY" | "OTHER";
export type ListingStatus = "PENDING" | "APPROVED" | "REJECTED" | "CLOSED";

export interface Listing {
  id: string;
  title: string;
  description: string;
  type: ListingType;
  category: Category;
  status: ListingStatus;
  rentalPrice: number | null;
  exchangeWish: string | null;
  condition: string | null;
  images: string[];
  rejectReason: string | null;
  userId: string;
  createdAt: string;
  updatedAt: string;
  user: {
    id: string;
    name: string;
    avatarUrl: string | null;
    rating: number;
  };
  isFavorited: boolean;
  _count: {
    favorites: number;
  };
}
