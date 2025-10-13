

export type ZarUser = {
    
    id: string,
    email: string,
    last_login_at: string | null,
    is_active: boolean,
    is_verified: boolean,
    updated_at: string,
    created_at: string
}


export type UserStats = {
  id: string;
  email: string;
  member_since: string;
  total_urls: number;
  favorite_urls: number;
  total_clicks: number;
  last_url_created: string | null;
  last_click_received: string | null;
};