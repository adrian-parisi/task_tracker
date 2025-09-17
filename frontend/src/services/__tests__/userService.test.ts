import { UserService, UserServiceError } from '../userService';
import { User } from '../../types/task';
import apiClient from '../apiClient';

// Mock the apiClient
jest.mock('../apiClient');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('UserService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('searchUsers', () => {
        const mockUsers: User[] = [
            {
                id: 1,
                username: 'john.doe',
                first_name: 'John',
                last_name: 'Doe',
                display_name: 'John Doe'
            },
            {
                id: 2,
                username: 'jane.smith',
                first_name: 'Jane',
                last_name: 'Smith',
                display_name: 'Jane Smith'
            }
        ];

        const mockResponse = {
            results: mockUsers,
            count: 2
        };

        it('should fetch users without search query', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockResponse });

            const result = await UserService.searchUsers();
            expect(result).toEqual(mockUsers);
            expect(mockApiClient.get).toHaveBeenCalledWith('/users/', { params: {} });
        });

        it('should fetch users with search query', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockResponse });

            const result = await UserService.searchUsers('john');
            expect(result).toEqual(mockUsers);
            expect(mockApiClient.get).toHaveBeenCalledWith('/users/', { 
                params: { search: 'john' } 
            });
        });

        it('should trim whitespace from search query', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockResponse });

            await UserService.searchUsers('  john  ');
            expect(mockApiClient.get).toHaveBeenCalledWith('/users/', { 
                params: { search: 'john' } 
            });
        });

        it('should handle empty search query', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockResponse });

            await UserService.searchUsers('');
            expect(mockApiClient.get).toHaveBeenCalledWith('/users/', { params: {} });
        });

        it('should handle 403 authorization error', async () => {
            const error = { response: { status: 403, data: { detail: 'Not authorized' } } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.searchUsers('john'))
                .rejects.toThrow('Not authorized to access user list');
        });

        it('should handle 500 server error', async () => {
            const error = { response: { status: 500, data: { detail: 'Server error' } } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.searchUsers('john'))
                .rejects.toThrow('Server error while searching users');
        });

        it('should handle generic errors', async () => {
            const error = { response: { status: 400, data: { detail: 'Bad request' } } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.searchUsers('john'))
                .rejects.toThrow('Failed to search users');
        });

        it('should handle network errors', async () => {
            const error = new Error('Network error');
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.searchUsers('john'))
                .rejects.toThrow('Failed to search users');
        });
    });

    describe('getUser', () => {
        const mockUser: User = {
            id: 1,
            username: 'john.doe',
            first_name: 'John',
            last_name: 'Doe',
            display_name: 'John Doe'
        };

        it('should fetch single user successfully', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockUser });

            const result = await UserService.getUser(1);
            expect(result).toEqual(mockUser);
            expect(mockApiClient.get).toHaveBeenCalledWith('/users/1/');
        });

        it('should handle 404 error with specific message', async () => {
            const error = { response: { status: 404 } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.getUser(1)).rejects.toThrow('User not found');
        });

        it('should handle 403 authorization error', async () => {
            const error = { response: { status: 403 } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.getUser(1))
                .rejects.toThrow('Not authorized to access user details');
        });

        it('should handle other errors with generic message', async () => {
            const error = { response: { status: 500 } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(UserService.getUser(1)).rejects.toThrow('Failed to fetch user');
        });
    });

    describe('UserServiceError', () => {
        it('should create error with message only', () => {
            const error = new UserServiceError('Test error');
            expect(error.message).toBe('Test error');
            expect(error.name).toBe('UserServiceError');
            expect(error.status).toBeUndefined();
            expect(error.details).toBeUndefined();
        });

        it('should create error with status and details', () => {
            const details = { field: 'username', message: 'Required' };
            const error = new UserServiceError('Validation error', 400, details);
            expect(error.message).toBe('Validation error');
            expect(error.status).toBe(400);
            expect(error.details).toEqual(details);
        });
    });
});