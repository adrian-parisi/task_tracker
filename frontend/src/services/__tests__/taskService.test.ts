import { TaskService, TaskServiceError } from '../taskService';
import { Task, TaskStatus, SmartSummaryResponse, SmartEstimateResponse, SmartRewriteResponse } from '../../types/task';
import apiClient from '../apiClient';

// Mock the apiClient
jest.mock('../apiClient');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('TaskService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('getTasks', () => {
        it('should fetch tasks successfully', async () => {
            const mockResponse = {
                results: [
                    {
                        id: '123e4567-e89b-12d3-a456-426614174000',
                        title: 'Test Task',
                        description: 'Test Description',
                        status: TaskStatus.TODO,
                        tags: [],
                        created_at: '2023-01-01T00:00:00Z',
                        updated_at: '2023-01-01T00:00:00Z'
                    }
                ],
                count: 1
            };

            mockApiClient.get.mockResolvedValue({ data: mockResponse });

            const result = await TaskService.getTasks();
            expect(result).toEqual(mockResponse);
            expect(mockApiClient.get).toHaveBeenCalledWith('/tasks/', { params: undefined });
        });

        it('should handle fetch tasks error', async () => {
            const error = { response: { status: 500, data: { detail: 'Server error' } } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(TaskService.getTasks()).rejects.toThrow(TaskServiceError);
        });

        it('should pass query parameters correctly', async () => {
            const params = { status: 'TODO', page: 1 };
            mockApiClient.get.mockResolvedValue({ data: { results: [], count: 0 } });

            await TaskService.getTasks(params);
            expect(mockApiClient.get).toHaveBeenCalledWith('/tasks/', { params });
        });
    });

    describe('getTask', () => {
        const taskId = '123e4567-e89b-12d3-a456-426614174000';
        const mockTask: Task = {
            id: taskId,
            title: 'Test Task',
            description: 'Test Description',
            status: TaskStatus.TODO,
            tags: [],
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z'
        };

        it('should fetch single task successfully', async () => {
            mockApiClient.get.mockResolvedValue({ data: mockTask });

            const result = await TaskService.getTask(taskId);
            expect(result).toEqual(mockTask);
            expect(mockApiClient.get).toHaveBeenCalledWith(`/tasks/${taskId}/`);
        });

        it('should handle 404 error with specific message', async () => {
            const error = { response: { status: 404 } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(TaskService.getTask(taskId)).rejects.toThrow('Task not found');
        });

        it('should handle other errors with generic message', async () => {
            const error = { response: { status: 500 } };
            mockApiClient.get.mockRejectedValue(error);

            await expect(TaskService.getTask(taskId)).rejects.toThrow('Failed to fetch task');
        });
    });

    describe('AI Tool Methods', () => {
        const taskId = '123e4567-e89b-12d3-a456-426614174000';

        describe('startSmartSummary', () => {
            it('should start smart summary generation successfully', async () => {
                const mockResponse = {
                    operation_id: '123e4567-e89b-12d3-a456-426614174000',
                    status: 'pending',
                    sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
                };

                mockApiClient.post.mockResolvedValue({ data: mockResponse });

                const result = await TaskService.startSmartSummary(taskId);
                expect(result).toEqual(mockResponse);
                expect(mockApiClient.post).toHaveBeenCalledWith(`/tasks/${taskId}/smart-summary/`);
            });

            it('should handle 404 error with specific message', async () => {
                const error = { response: { status: 404 } };
                mockApiClient.post.mockRejectedValue(error);

                await expect(TaskService.startSmartSummary(taskId))
                    .rejects.toThrow('Task not found for summary generation');
            });

            it('should handle other errors with generic message', async () => {
                const error = { response: { status: 500 } };
                mockApiClient.post.mockRejectedValue(error);

                await expect(TaskService.startSmartSummary(taskId))
                    .rejects.toThrow('Failed to start smart summary generation');
            });
        });

        describe('getSmartEstimate', () => {
            it('should fetch smart estimate successfully', async () => {
                const mockResponse: SmartEstimateResponse = {
                    suggested_points: 5,
                    confidence: 0.75,
                    similar_task_ids: ['456e7890-e89b-12d3-a456-426614174001'],
                    rationale: 'Based on similar tasks with same assignee'
                };

                mockApiClient.get.mockResolvedValue({ data: mockResponse });

                const result = await TaskService.getSmartEstimate(taskId);
                expect(result).toEqual(mockResponse);
                expect(mockApiClient.get).toHaveBeenCalledWith(`/tasks/${taskId}/smart-estimate/`);
            });

            it('should handle 404 error with specific message', async () => {
                const error = { response: { status: 404 } };
                mockApiClient.get.mockRejectedValue(error);

                await expect(TaskService.getSmartEstimate(taskId))
                    .rejects.toThrow('Task not found for estimate calculation');
            });
        });

        describe('getSmartRewrite', () => {
            it('should fetch smart rewrite successfully', async () => {
                const mockResponse: SmartRewriteResponse = {
                    title: 'Enhanced Task Title',
                    user_story: 'As a user, I want to complete this task so that I can achieve my goal.'
                };

                mockApiClient.post.mockResolvedValue({ data: mockResponse });

                const result = await TaskService.getSmartRewrite(taskId);
                expect(result).toEqual(mockResponse);
                expect(mockApiClient.post).toHaveBeenCalledWith(`/tasks/${taskId}/smart-rewrite/`);
            });

            it('should handle 404 error with specific message', async () => {
                const error = { response: { status: 404 } };
                mockApiClient.post.mockRejectedValue(error);

                await expect(TaskService.getSmartRewrite(taskId))
                    .rejects.toThrow('Task not found for rewrite generation');
            });
        });
    });

    describe('CRUD Operations', () => {
        it('should create task successfully', async () => {
            const newTask = { title: 'New Task', description: 'New Description' };
            const createdTask: Task = {
                id: '123e4567-e89b-12d3-a456-426614174000',
                title: 'New Task',
                description: 'New Description',
                status: TaskStatus.TODO,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            };

            mockApiClient.post.mockResolvedValue({ data: createdTask });

            const result = await TaskService.createTask(newTask);
            expect(result).toEqual(createdTask);
            expect(mockApiClient.post).toHaveBeenCalledWith('/tasks/', newTask);
        });

        it('should update task successfully', async () => {
            const taskId = '123e4567-e89b-12d3-a456-426614174000';
            const updates = { title: 'Updated Task' };
            const updatedTask: Task = {
                id: taskId,
                title: 'Updated Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T01:00:00Z'
            };

            mockApiClient.patch.mockResolvedValue({ data: updatedTask });

            const result = await TaskService.updateTask(taskId, updates);
            expect(result).toEqual(updatedTask);
            expect(mockApiClient.patch).toHaveBeenCalledWith(`/tasks/${taskId}/`, updates);
        });

        it('should delete task successfully', async () => {
            const taskId = '123e4567-e89b-12d3-a456-426614174000';
            mockApiClient.delete.mockResolvedValue({ data: undefined });

            await expect(TaskService.deleteTask(taskId)).resolves.toBeUndefined();
            expect(mockApiClient.delete).toHaveBeenCalledWith(`/tasks/${taskId}/`);
        });
    });
});