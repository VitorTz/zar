

export type UrlResponse = {
    
    id: number
    domain_id: number
    user_id: string | null
    original_url: string
    short_url: string
    short_code: string
    clicks: 0
    is_favorite: false
    created_at: Date
    expires_at: Date | null
    
}