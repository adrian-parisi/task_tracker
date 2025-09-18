import apiClient from './apiClient';
import { 
    Task, 
    TaskListResponse, 
    SmartSummaryResponse, 
    SmartEstimateResponse, 
    SmartRewriteResponse 
} from '../types/task';

// Custom error class for better error handling
export class TaskServiceError extends Error {
    constructor(
        message: string,
        public status?: number,
        public details?: any
    ) {
        super(message);
        this.name = 'TaskServiceError';
    }
}

export class TaskService {
    static async getTasks(params?: {
        status?: string;
        assignee?: number;
        page?: number;
    }): Promise<TaskListResponse> {
        try {
            const response = await apiClient.get('/tasks/', { params });
            return response.data;
        } catch (error: any) {
            throw new TaskServiceError(
                'Failed to fetch tasks',
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async getTask(id: string): Promise<Task> {
        try {
            const response = await apiClient.get(`/tasks/${id}/`);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found' 
                : 'Failed to fetch task';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async createTask(task: Partial<Task>): Promise<Task> {
        try {
            const response = await apiClient.post('/tasks/', task);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 400 
                ? 'Invalid task data' 
                : 'Failed to create task';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async updateTask(id: string, task: Partial<Task>): Promise<Task> {
        try {
            const response = await apiClient.patch(`/tasks/${id}/`, task);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found' 
                : error.response?.status === 400
                ? 'Invalid task data'
                : 'Failed to update task';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async deleteTask(id: string): Promise<void> {
        try {
            await apiClient.delete(`/tasks/${id}/`);
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found' 
                : 'Failed to delete task';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    // AI Tool Methods - Now async operations
    static async startSmartSummary(taskId: string): Promise<{
        operation_id: string;
        status: string;
        sse_url: string;
    }> {
        try {
            const response = await apiClient.post(`/tasks/${taskId}/smart-summary/`);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found for summary generation' 
                : 'Failed to start smart summary generation';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async getSmartEstimate(taskId: string): Promise<SmartEstimateResponse> {
        try {
            const response = await apiClient.post(`/tasks/${taskId}/smart-estimate/`);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found for estimate calculation' 
                : 'Failed to get smart estimate';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }

    static async getSmartRewrite(taskId: string): Promise<SmartRewriteResponse> {
        try {
            const response = await apiClient.post(`/tasks/${taskId}/smart-rewrite/`);
            return response.data;
        } catch (error: any) {
            const message = error.response?.status === 404 
                ? 'Task not found for rewrite generation' 
                : 'Failed to get smart rewrite';
            throw new TaskServiceError(
                message,
                error.response?.status,
                error.response?.data
            );
        }
    }
}