

export type ZarUser = {
  id: string;
  email: string;
  last_login_at?: string | null;
  is_active: boolean;
  is_verified: boolean;
  updated_at: string;
  created_at: string;
};

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


export type UserLogin = { 
  email: string; 
  password: string 
};


export type UserCreate = { 
  email: string; 
  password: string 
};


export type UserSession = {

  user_id: string
  issued_at: string
  expires_at: string
  revoked: boolean
  revoked_at: string | null
  device_name: string | null
  device_ip: string
  user_agent: string | null
  last_used_at: string

}

export type UserSessionPagination = {

  total: number
  limit: number
  offset: number
  page: number
  pages: number
  results: UserSession[]

}