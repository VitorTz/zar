

export type UrlStats = {
  short_code: string;
  total_clicks: number;
  unique_visitors: number;
  first_click: string | null;
  last_click: string | null;
  timeline: { day: string; clicks: number }[];
  devices: Record<string, number>;
  browsers: Record<string, number>;
  top_countries: { country_code: string; clicks: number }[];
  top_cities: { city: string; clicks: number }[];
  operating_systems: Record<string, number>;
  top_referers: { referer: string; clicks: number }[];
};