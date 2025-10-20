

export interface TopURL {
  short_code: string;
  short_url: string;
  title?: string | null;
  clicks: number;
  original_url: string;
}

export interface TopTag {
  tag_name: string;
  usage_count: number;
  tag_color: string;
}

export interface TopCountry {
  country_code: string;
  clicks: number;
}

export interface TimelineEntry {
  date: string;
  new_urls: number;
  new_users: number;
  total_clicks: number;
}

export type DashboardStats = {
  // URLs
  total_urls: number;
  favorite_urls: number;
  custom_alias_urls: number;
  protected_urls: number;
  expiring_urls: number;
  urls_created_last_24h: number;
  urls_created_last_7d: number;
  urls_created_last_30d: number;
  total_clicks: number;
  avg_clicks_per_url: number;
  max_clicks_single_url: number;

  // Users
  total_users: number;
  verified_users: number;
  new_users_last_7d: number;
  new_users_last_30d: number;
  users_active_last_24h: number;
  users_active_last_7d: number;

  // Analytics
  clicks_last_hour: number;
  clicks_last_24h: number;
  clicks_last_7d: number;
  clicks_last_30d: number;
  unique_visitors_24h: number;
  unique_visitors_7d: number;
  countries_reached_30d: number;

  // Sessions
  active_sessions: number;
  users_with_active_sessions: number;
  sessions_active_last_hour: number;

  // Tags
  total_tags: number;
  top_tags: TopTag[];

  // Aggregated JSON fields
  top_urls: TopURL[];
  device_distribution: Record<string, number>;
  top_countries: TopCountry[];
  growth_timeline: TimelineEntry[];

  // Metadata
  last_updated: string; // ISO datetime string
  last_updated_formatted: string;
}