import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { URLCreate, URLResponse, URLStatsResponse, UrlPagination } from '../model/Url';
import { ZarUser, UserCreate, UserLogin, UserStats, UserSessionPagination } from '../model/User';
import { DashboardStats } from '../model/DashboardStats';


class ZarApiClient {

  private http: AxiosInstance;
  private urlStatsHeader = { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache', 'Expires': '0' }

  constructor(baseURL = "/api/v1", config?: AxiosRequestConfig) {
    this.http = axios.create({
      baseURL,
      withCredentials: true,
      ...config,
    });
  }

  getPagination(page: number): { limit: number; offset: number } {
    const limit = 64;
    const offset = (page - 1) * limit;
    return { limit, offset };
  }
  
  setCookieHeaderManually(accessToken?: string | null, refreshToken?: string | null) {
    const parts: string[] = [];
    if (accessToken) parts.push(`access_token=${accessToken}`);
    if (refreshToken) parts.push(`refresh_token=${refreshToken}`);
    if (parts.length) {
      this.http.defaults.headers.common["Cookie"] = parts.join("; ");
    } else {
      delete this.http.defaults.headers.common["Cookie"];
    }
  }
  
  setWithCredentials(enabled: boolean) {
    this.http.defaults.withCredentials = enabled;
  }
  
  async shortenUrl(payload: URLCreate): Promise<URLResponse> {
    const r = await this.http.post<URLResponse>("/url", payload);
    return r.data;
  }

  async getUrlStats(short_code: string): Promise<URLStatsResponse> {
    const r = await this.http.get<URLStatsResponse>(
      `/url/${short_code}/stats`, 
      { headers: this.urlStatsHeader }
    );
    return r.data;
  }
  
  async getUserUrls(page: number = 1): Promise<UrlPagination> {
    const { limit, offset } = this.getPagination(page)
    const r = await this.http.get<UrlPagination>(`/user/urls/?limit=${limit}&offset=${offset}`);
    return r.data;
  }
  
  async login(payload: UserLogin): Promise<ZarUser> {
    const r = await this.http.post<ZarUser>("/auth/login", payload);
    return r.data;
  }

  async signup(payload: UserCreate): Promise<any> {
    const r = await this.http.post("/auth/signup", payload);
    return r.data;
  }

  async logout(): Promise<any> {
    const r = await this.http.post("/auth/logout");
    return r.data;
  }

  async logoutAll(): Promise<any> {
    const r = await this.http.post("/auth/logout/all");
    return r.data;
  }

  async refreshSession(): Promise<ZarUser> {
    const r = await this.http.post<ZarUser>("/auth/refresh");
    return r.data;
  }  

  async getSessions(): Promise<UserSessionPagination> {
    const r = await this.http.get<UserSessionPagination>("/auth/sessions")
    return r.data
  }

  async getMe(): Promise<ZarUser> {
    const r = await this.http.get<ZarUser>("/auth/me");
    return r.data;
  }

  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getMe();
      return true;
    } catch {
      return false;
    }
  }

  async getUserStats(): Promise<UserStats> {
    const r = await this.http.get<UserStats>("/user/stats")
    return r.data
  }

  async setFavorite(short_code: string, is_favorite = true): Promise<URLResponse> {
    const payload = { short_code, is_favorite };
    const r = await this.http.put<URLResponse>("/user/url/favorite", payload);
    return r.data;
  }

  async assignUrlToUser(payload: { short_code: string }): Promise<any> {
    const r = await this.http.post("/user/url", payload);
    return r.data;
  }

  async deleteUserUrl(short_code: string): Promise<any> {
    const r = await this.http.delete("/user/url", { data: { short_code } });
    return r.data;
  }
  
  async getDashboardStats(): Promise<DashboardStats> {
    const r = await this.http.get<DashboardStats>("/dashboard/stats");
    return r.data;
  }
  
  async request<T = any>(cfg: AxiosRequestConfig) {
    return this.http.request<T>(cfg).then((r) => r.data);
  }
}


export const api = new ZarApiClient("http://localhost:8000")
