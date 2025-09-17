import apiClient from './apiClient';

export interface User {
    id: number;
    username: string;
    email: string;
}

export interface LoginResponse {
    success: boolean;
    user?: User;
    error?: string;
}

export interface CurrentUserResponse {
    authenticated: boolean;
    user?: User;
}

export class AuthService {
    static async login(username: string, password: string): Promise<LoginResponse> {
        try {
            const response = await apiClient.post('/auth/login/', {
                username,
                password
            });
            return response.data;
        } catch (error: any) {
            if (error.response?.data?.error) {
                return { success: false, error: error.response.data.error };
            }
            return { success: false, error: 'Login failed' };
        }
    }

    static async logout(): Promise<void> {
        try {
            await apiClient.post('/auth/logout/');
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    static async getCurrentUser(): Promise<CurrentUserResponse> {
        try {
            const response = await apiClient.get('/auth/user/');
            return response.data;
        } catch (error) {
            return { authenticated: false };
        }
    }
}