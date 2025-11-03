

export interface URLCreate {
  url: string;
  title?: string | null;
  descr?: string | null;
  is_favorite?: boolean | null;
}


export interface URLResponse {
  id: number;
  title: string | null;
  descr: string | null;
  domain_id: number;
  user_id?: string | null;
  original_url: string;
  short_url: string;
  tags: UrlTag[]
  short_code: string;
  clicks: number;
  is_favorite?: boolean | null;
  created_at: string;
}


export interface UrlStats {
  url_id: number;
  total_clicks: number;
  unique_visitors: number;
  first_click: string | null;
  last_click: string | null;
  clicks_today: number;
  browsers?: string[];
  operating_systems?: string[];
  device_types?: string[];
  countries?: string[];
}


export interface UrlTagCreate {
  name: string;
  color?: string | null;
  descr?: string | null;
}


export interface UrlTag {
  id: number;
  user_id: string;
  name: string;
  color: string;
  descr?: string | null;
  created_at: string;
}


export interface UrlTagUpdate {
  id: number;
  name?: string | null;
  color?: string | null;
  descr?: string | null;
}
