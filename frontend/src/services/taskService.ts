import apiClient from './apiClient';
import { 
    Task, 
    TaskListResponse, 
    SmartSummaryResponse, 
    SmartEstimateResponse, 
    SmartRewriteResponse 
} from '../types/task';

export class TaskService {
    static async getTasks(params?: {
        status?: string;
        assignee?: number;
        tag?: string;
        page?: number;
    }): Promise<TaskListResponse> {
        const response = await apiClient.get('/tasks/', { params });
        return response.data;
    }

    static async getTask(id: string): Promise<Task> {
        const response = await apiClient.get(`/tasks/${id}/`);
        return response.data;
    }

    static async createTask(task: Partial<Task>): Promise<Task> {
        const response = await apiClient.post('/tasks/', task);
        return response.data;
    }

    static async updateTask(id: string, task: Partial<Task>): Promise<Task> {
        const response = await apiClient.patch(`/tasks/${id}/`, task);
        return response.data;
    }

    static async deleteTask(id: string): Promise<void> {
        await apiClient.delete(`/tasks/${id}/`);
    }

    // AI Tool Methods
    static async getSmartSummary(taskId: string): Promise<SmartSummaryResponse> {
        const response = await apiClient.get(`/tasks/${taskId}/smart-summary/`);
        return response.data;
    }

    static async getSmartEstimate(taskId: string): Promise<SmartEstimateResponse> {
        const response = await apiClient.get(`/tasks/${taskId}/smart-estimate/`);
        return response.data;
    }

    static async getSmartRewrite(taskId: string): Promise<SmartRewriteResponse> {
        const response = await apiClient.post(`/tasks/${taskId}/smart-rewrite/`);
        return response.data;
    }
}