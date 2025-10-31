import type { AxiosInstance } from "axios";
import type { Dashboard } from "../types/dashboard";


export class DashboardService {

    private client: AxiosInstance

    constructor(client: AxiosInstance) {
        this.client = client
    }

    async getDashboard(): Promise<Dashboard> {
        try {
          const response = await this.client.get<Dashboard>('/api/v1/dashboard/data');
          return response.data;
        } catch (error) {
          throw error;
        }
    }
    
    async refreshDashboard(): Promise<Dashboard> {
        try {
          const response = await this.client.put<Dashboard>('/api/v1/dashboard/refresh');
          return response.data;
        } catch (error) {
          throw error;
        }
    }

}