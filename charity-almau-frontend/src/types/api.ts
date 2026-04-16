export interface ApiResponse<T> {
  success: true;
  data: T;
  meta?: { page: number; limit: number; total: number; totalPages: number };
}

export interface ApiError {
  success: false;
  error: { code: string; message: string };
}

export type ApiResult<T> = ApiResponse<T> | ApiError;
