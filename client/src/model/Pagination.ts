import { UrlPagination } from "./Url";


export type Pagination = {
    total: number;
    limit: number;
    offset: number;
    page: number;
    pages: number;
}

export function emptyPagination(): Pagination {
    return {
        total: 0,
        limit: 64,
        offset: 0,
        page: 1,
        pages: 0
    }
}


export function extractNextPagination(pagination: UrlPagination): Pagination {
    return {
        total: pagination.total + 1,
        limit: pagination.limit,
        offset: pagination.offset,
        page: pagination.page,
        pages: pagination.pages
    }
}