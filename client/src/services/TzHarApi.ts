import { AuthService } from "./AuthService";
import { URLService } from "./URLService";
import { TagService } from "./TagService";
import { DashboardService } from "./DashboardService";
import axios, {type AxiosInstance, AxiosError } from "axios";
import { TzHarAPIError } from "./TzHarAPIError";



export class TzHarAPIClient {

  private client: AxiosInstance;
  auth: AuthService
  url: URLService
  tag: TagService
  dashboard: DashboardService

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        return this.handleError(error);
      }
    );

    this.auth = new AuthService(this.client)
    this.url = new URLService(this.client)
    this.tag = new TagService(this.client)
    this.dashboard = new DashboardService(this.client)
  }

  private handleError(error: AxiosError): Promise<never> {
    if (error.response) {
      const status = error.response.status;
      const data: any = error.response.data;

      if (status === 422 && data.detail) {
        const validationErrors = data.detail
          .map((err: any) => `${err.loc.join('.')}: ${err.msg}`)
          .join(', ');
        throw new TzHarAPIError(status, `Validation Error: ${validationErrors}`, data.detail);
      }
    
      const message = data.detail || data.message || error.message;
      throw new TzHarAPIError(status, message, data);
    } else if (error.request) {
      throw new TzHarAPIError(0, 'Network error: No response from server', error);
    } else {
      throw new TzHarAPIError(0, error.message, error);
    }
  }

}


export const api = new TzHarAPIClient('http://localhost:8000');