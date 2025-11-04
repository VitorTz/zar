
interface UserStats {
  total: number;
  new_30d: number;
  new_7d: number;
  active_30d: number;
  active_7d: number;
  active_24h: number;
}

interface UrlStats {
  total: number;
  new_30d: number;
  new_7d: number;
  new_24h: number;
  avg_clicks: number;
  median_clicks: number;
}

interface ClickStats {
  total: number;
  last_30d: number;
  last_7d: number;
  last_24h: number;
}

interface AnalyticsStats {
  total_records: number;
  records_30d: number;
  records_7d: number;
  records_24h: number;
  unique_visitors_all_time: number;
  unique_visitors_30d: number;
  countries_reached: number;
}

interface TopUrl {
  short_code: string;
  original_url: string;
  clicks: number;
  created_at: string | Date;
}

interface TopCountry {
  country_code: string;
  clicks: number;
  percentage: number;
}

interface Geography {
  top_countries: TopCountry[];
}

interface DeviceBreakdown {
  mobile: number;
  desktop: number;
  tablet: number;
  other: number;
}

interface BrowserStat {
  browser: string;
  count: number;
}

interface ClientInfo {
  devices: DeviceBreakdown;
  browsers: BrowserStat[];
}

interface TopTag {
  name: string;
  usage_count: number;
}

interface TagStats {
  total_tags: number;
  urls_with_tags: number;
  avg_tags_per_url: number;
  top_tags: TopTag[];
}

interface TopDomain {
  domain: string;
  url_count: number;
  total_clicks: number;
}

interface DomainStats {
  total_domains: number;
  top_domains: TopDomain[];
}

interface DailyGrowthItem {
  date: string | Date;
  new_urls: number;
  new_users: number;
  clicks: number;
}

interface SessionStats {
  total: number;
  active: number;
  revoked: number;
  users_with_sessions: number;
  avg_duration_hours: number;
}

interface ConversionStats {
  urls_with_clicks: number;
  total_urls_30d: number;
  conversion_rate: number;
  urls_10plus_rate: number;
}

export interface Dashboard {

  total_urls: number;
  last_updated: string | Date;
  users: UserStats;
  urls: UrlStats;
  clicks: ClickStats;
  analytics: AnalyticsStats;
  top_urls: TopUrl[];
  geography: Geography;
  client_info: ClientInfo;
  tags: TagStats;
  domains: DomainStats;
  daily_growth: DailyGrowthItem[];
  sessions: SessionStats;
  conversion: ConversionStats;
  
}
