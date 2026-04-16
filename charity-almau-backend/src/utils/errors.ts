export class AppError extends Error {
  public statusCode: number;
  public code: string;

  constructor(code: string, message: string, statusCode: number = 400) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.name = 'AppError';
  }
}

// Auth
export const AUTH_REQUIRED = (msg = 'Authentication required') =>
  new AppError('AUTH_REQUIRED', msg, 401);
export const AUTH_INVALID_TOKEN = (msg = 'Invalid or expired token') =>
  new AppError('AUTH_INVALID_TOKEN', msg, 401);
export const AUTH_NOT_ALMAU_EMAIL = (msg = 'Only @almau.edu.kz emails are allowed') =>
  new AppError('AUTH_NOT_ALMAU_EMAIL', msg, 403);
export const AUTH_MSAL_FAILED = (msg = 'Microsoft authentication failed') =>
  new AppError('AUTH_MSAL_FAILED', msg, 401);

// Authorization
export const FORBIDDEN = (msg = 'Forbidden') =>
  new AppError('FORBIDDEN', msg, 403);
export const ADMIN_REQUIRED = (msg = 'Admin access required') =>
  new AppError('ADMIN_REQUIRED', msg, 403);

// Validation
export const VALIDATION_ERROR = (msg = 'Validation error') =>
  new AppError('VALIDATION_ERROR', msg, 400);
export const BAD_WORDS_DETECTED = (msg = 'Inappropriate language detected') =>
  new AppError('BAD_WORDS_DETECTED', msg, 400);

// Listings
export const LISTING_NOT_FOUND = (msg = 'Listing not found') =>
  new AppError('LISTING_NOT_FOUND', msg, 404);
export const LISTING_NOT_OWNER = (msg = 'You are not the owner of this listing') =>
  new AppError('LISTING_NOT_OWNER', msg, 403);
export const LISTING_ALREADY_CLOSED = (msg = 'Listing is already closed') =>
  new AppError('LISTING_ALREADY_CLOSED', msg, 400);
export const LISTING_NOT_APPROVED = (msg = 'Listing is not approved') =>
  new AppError('LISTING_NOT_APPROVED', msg, 400);

// Requests
export const REQUEST_NOT_FOUND = (msg = 'Request not found') =>
  new AppError('REQUEST_NOT_FOUND', msg, 404);
export const REQUEST_ALREADY_EXISTS = (msg = 'You already sent a request for this listing') =>
  new AppError('REQUEST_ALREADY_EXISTS', msg, 409);
export const REQUEST_OWN_LISTING = (msg = 'Cannot request your own listing') =>
  new AppError('REQUEST_OWN_LISTING', msg, 400);
export const REQUEST_NOT_PENDING = (msg = 'Request is no longer pending') =>
  new AppError('REQUEST_NOT_PENDING', msg, 400);

// Chat
export const CHATROOM_NOT_FOUND = (msg = 'Chat room not found') =>
  new AppError('CHATROOM_NOT_FOUND', msg, 404);
export const CHATROOM_NOT_MEMBER = (msg = 'You are not a member of this chat room') =>
  new AppError('CHATROOM_NOT_MEMBER', msg, 403);

// Users
export const USER_NOT_FOUND = (msg = 'User not found') =>
  new AppError('USER_NOT_FOUND', msg, 404);

// Ratings
export const RATING_ALREADY_EXISTS = (msg = 'You already rated this user for this listing') =>
  new AppError('RATING_ALREADY_EXISTS', msg, 409);
export const RATING_SELF = (msg = 'You cannot rate yourself') =>
  new AppError('RATING_SELF', msg, 400);
export const RATING_INVALID_SCORE = (msg = 'Score must be between 1 and 5') =>
  new AppError('RATING_INVALID_SCORE', msg, 400);

// Favorites
export const FAVORITE_ALREADY_EXISTS = (msg = 'Already in favorites') =>
  new AppError('FAVORITE_ALREADY_EXISTS', msg, 409);
export const FAVORITE_NOT_FOUND = (msg = 'Favorite not found') =>
  new AppError('FAVORITE_NOT_FOUND', msg, 404);

// Upload
export const UPLOAD_TOO_LARGE = (msg = 'File is too large') =>
  new AppError('UPLOAD_TOO_LARGE', msg, 400);
export const UPLOAD_INVALID_TYPE = (msg = 'Invalid file type. Only JPEG, PNG, and WebP are allowed') =>
  new AppError('UPLOAD_INVALID_TYPE', msg, 400);
export const UPLOAD_TOO_MANY_FILES = (msg = 'Too many files') =>
  new AppError('UPLOAD_TOO_MANY_FILES', msg, 400);

// AI
export const AI_SERVICE_UNAVAILABLE = (msg = 'AI service is unavailable') =>
  new AppError('AI_SERVICE_UNAVAILABLE', msg, 503);
export const AI_INVALID_IMAGE = (msg = 'Invalid image for AI analysis') =>
  new AppError('AI_INVALID_IMAGE', msg, 400);

// Generic
export const INTERNAL_ERROR = (msg = 'Internal server error') =>
  new AppError('INTERNAL_ERROR', msg, 500);
export const NOT_FOUND = (msg = 'Not found') =>
  new AppError('NOT_FOUND', msg, 404);
