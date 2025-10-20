


export type URLCreate = {
  url: string;
  title?: string | null;
  password?: string | null;
  expires_at?: string | null;
  is_favorite?: boolean | null;
};


export type URLResponse = {
  user_id: string | null;
  original_url: string;
  short_url: string;
  short_code: string;
  clicks: number;
  has_password: boolean;
  qrcode_url: string;
  title: string | null
  is_favorite?: boolean;
  created_at?: string | null;
  expires_at?: string | null;
};

export type UrlPagination = {
  total: number;
  limit: number;
  offset: number;
  page: number;
  pages: number;
  results: URLResponse[];
};

export type URLStatsResponse = {
  short_code: string;
  total_clicks: number;
  unique_visitors: number;
  first_click?: string | null;
  last_click?: string | null;
  timeline?: { day: string; clicks: number }[];
  devices?: Record<string, number>;
  browsers?: Record<string, number>;
  operating_systems?: Record<string, number>;
  top_countries?: { country_code: string; clicks: number }[];
  top_cities?: { city: string; clicks: number }[];
  top_referers?: { referer: string; clicks: number }[];
};
