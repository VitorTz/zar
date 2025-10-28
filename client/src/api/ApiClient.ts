import axios from 'axios';
import type { UserLogin } from "./models/UserLogin";
import type { UserSignUp } from "./models/UserSignUp";
import type { AxiosResponse } from "axios";
import type { User } from "./models/User";
import type { Sessions } from "./models/Sessions";
import type { Pagination } from './models/Pagination';
import type { UrlResponse } from './models/UrlResponse';
import type { DeleteUrl } from './models/DeleteUrl';


const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});


api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Refresh token failed', refreshError);
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);


class AuthService {

    private prefix = "/auth/"

    async login(credentias: UserLogin): Promise<User> {
        const response = await api.post(this.prefix + "login", credentias)
        return response.data
    }

    async signup(credentias: UserSignUp): Promise<AxiosResponse> {
        return await api.post(this.prefix + "signup", credentias)
    }

    async me(): Promise<User> {
        const response = await api.get(this.prefix + "me")
        return response.data
    }

    async sessions(): Promise<Sessions> {
        const response = await api.get(this.prefix + "sessions")
        return response.data
    }

    async refresh(): Promise<User> {
        const response = await api.post(this.prefix + "refresh")
        return response.data
    }

    async logout(): Promise<number> {
        const response = await api.post(this.prefix + "logout")
        return response.status
    }

    async logoutAll(): Promise<number> {
        const response = await api.post(this.prefix + "logout/all")
        return response.status
    }

}

class UserService {

    private prefix = "/user/"

    async getUrls(limit: number = 64, offset: number = 0): Promise<Pagination<UrlResponse>> {
        const response = await api.get(this.prefix + `url/?limit=${limit}&offset=${offset}`)
        return response.data
    }

    async deleteUrl(url: DeleteUrl): Promise<number> {
        const response = await api.delete(this.prefix + 'url', {data: url})
        return response.status
    }
}


class ApiClient {

    auth = new AuthService()
    user = new UserService()
}


export const apiClient = new ApiClient()
