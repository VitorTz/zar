import type { AxiosInstance } from "axios";
import type { URLResponse, UrlTag, UrlTagCreate, UrlTagUpdate } from "../types/URL";
import type { Pagination } from "../types/pagination";


export class TagService {

    private client: AxiosInstance

    constructor(client: AxiosInstance) {
        this.client = client
    }

    async getUserTags(limit: number = 64, offset: number = 0): Promise<Pagination<UrlTag>> {
       try {
         const response = await this.client.get<Pagination<UrlTag>>('/api/v1/user/tags/', {
           params: { limit, offset },
         });
         return response.data;
       } catch (error) {
         throw error;
       }
    }
   
    async createTag(data: UrlTagCreate): Promise<UrlTag> {
       try {
         const response = await this.client.post<UrlTag>('/api/v1/user/tags/', data);
         return response.data;
       } catch (error) {
         throw error;
       }
    }
   
    async updateTag(data: UrlTagUpdate): Promise<UrlTag> {
       try {
         const response = await this.client.put<UrlTag>('/api/v1/user/tags/', data);
         return response.data;
       } catch (error) {
         throw error;
       }
    }
   
    async deleteTag(id: number): Promise<void> {
       try {
         await this.client.delete('/api/v1/user/tags/', {
           data: { id },
         });
       } catch (error) {
         throw error;
       }
    }
   
    async getUrlsFromTag(tagId: number, limit: number = 64, offset: number = 0): Promise<Pagination<URLResponse>> {
       try {
         const response = await this.client.get<Pagination<URLResponse>>('/api/v1/user/tags/relations', {
           params: { limit, offset, id: tagId }, // Corrigido para enviar tagId como param
         });
         return response.data;
       } catch (error) {
         throw error;
       }
    }
   
    async createUrlTagRelation(urlId: number, tagId: number): Promise<void> {
       try {
         await this.client.post('/api/v1/user/tags/relations', {
           url_id: urlId,
           tag_id: tagId,
         });
       } catch (error) {
         throw error;
       }
    }
   
    async deleteUrlTagRelation(urlId: number, tagId: number): Promise<void> {
       try {
         await this.client.delete('/api/v1/user/tags/relations', {
           data: {
             url_id: urlId,
             tag_id: tagId,
           },
         });
       } catch (error) {
         throw error;
       }
    }
   
    async clearTag(tagId: number): Promise<void> {
       try {
         await this.client.delete('/api/v1/user/tags/relations/clear', {
           data: { id: tagId },
         });
       } catch (error) {
         throw error;
       }
    }
}