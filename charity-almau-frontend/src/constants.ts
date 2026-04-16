import type { ListingType, Category, ListingStatus } from './types/listing';
import type { RequestStatus } from './types/request';

export const LISTING_TYPES: ListingType[] = ['FREE', 'EXCHANGE', 'RENT'];

export const CATEGORIES: Category[] = [
  'TEXTBOOKS', 'TECH', 'FURNITURE', 'CLOTHING', 'SPORTS', 'STATIONERY', 'OTHER',
];

export const LISTING_STATUSES: ListingStatus[] = ['PENDING', 'APPROVED', 'REJECTED', 'CLOSED'];

export const REQUEST_STATUSES: RequestStatus[] = ['PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED'];

export const API_URL = import.meta.env.VITE_API_URL as string;
export const WS_URL = import.meta.env.VITE_WS_URL as string;

export const getImageUrl = (path: string): string => `${API_URL}${path}`;

export const getAvatarUrl = (avatarUrl: string | null): string | null =>
  avatarUrl ? `${API_URL}${avatarUrl}` : null;
