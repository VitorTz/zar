

export interface Pagination<T> {
  total: number;
  limit: number;
  offset: number;
  page?: number | null;
  pages?: number | null;
  results: T[];
}
