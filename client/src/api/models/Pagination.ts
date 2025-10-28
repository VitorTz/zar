

export type Pagination<T> = {
    
    total: number
    limit: number
    page: number
    pages: number
    offset: number
    results: T[]

}