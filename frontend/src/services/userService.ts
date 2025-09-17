import apiClient from './apiClient';
import { User } from '../types/task';

// Response interface for user list API
export interface UserListResponse {
    results: User[];
    count: number;
    next?: string;
    previous?: string;
}

// Custom error class for better error handling
export class UserServiceError extends Error {
    constructor(
        message: string,
        public status?: number,
        public details?: any
    ) {
        super(message);
        this.name = 'UserServiceError';
    }
}

export class UserService {
    /**
     * Search users by query string
     * @param query Optional search query to filter users by username, first_name, or last_name
     * @returns Promise<User[]> Array of users matching the search criteria
     */
    static async searchUsers(query?: string): Promise<User[]> {
        try {
            const params: { search?: string } = {};
            if (query && query.trim()) {
                params.search = query.trim();
            }

            const response = await apiClient.get('/users/', { params });
            const data: UserListResponse = response.data;
            return data.results;
        } catch (error: any) {
            const message = error.response?.status === 403 
                ? 'Not authorized to access user list' 
                : error.response?.status === 500
                ? 'Server error while searching users'
                : 'Failed to search users';
            
            throw new UserServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    /**
     * Get a specific user by ID
     * @param id User ID
     * @returns Promise<User> User object
     */
    static async getUser(id: number): Promise<User> {
        try {
            const response = await apiClient.get(`/users/${id}/`);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'User not found' 
                : error.response?.status === 403
                ? 'Not authorized to access user details'
                : 'Failed to fetch user';
            
            throw new UserServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }
}