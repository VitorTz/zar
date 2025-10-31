import type { AxiosInstance } from "axios";
import type { URLResponse, URLCreate, UrlStats } from "../types/URL";
import type { Pagination } from "../types/pagination";


export class URLService {

    private client: AxiosInstance

    constructor(client: AxiosInstance) {
        this.client = client
    }

    async shortenUrl(data: URLCreate): Promise<URLResponse> {
        try {
          const response = await this.client.post<URLResponse>('/api/v1/', data);
          return response.data;
        } catch (error) {
          throw error;
        }
    }
    
    async redirectFromShortCode(shortCode: string): Promise<void> {
        try {
          await this.client.get(`/api/v1/${shortCode}`);
        } catch (error) {
          throw error;
        }
    }
    
    async getUrlStats(shortCode: string): Promise<UrlStats> {
        try {
          const response = await this.client.get<UrlStats>(`/api/v1/${shortCode}/stats`);
          return response.data;
        } catch (error) {
          throw error;
        }
    }
    
    async getUserUrls(limit: number = 64, offset: number = 0): Promise<Pagination<URLResponse>> {
        try {
          const response = await this.client.get<Pagination<URLResponse>>('/api/v1/user/url', {
            params: { limit, offset },
          });
          return response.data;
        } catch (error) {
          throw error;
        }
    }
    
    async deleteUserUrl(id: number): Promise<void> {
        try {
          await this.client.delete('/api/v1/user/url', {
            data: { id },
          });
        } catch (error) {
          throw error;
        }
    }
    
    async setFavoriteUrl(urlId: number, isFavorite: boolean): Promise<void> {
        try {
            await this.client.put('/api/v1/user/url/favorite', {
            url_id: urlId,
            is_favorite: isFavorite,
            });
        } catch (error) {
            throw error;
        }
    }

}