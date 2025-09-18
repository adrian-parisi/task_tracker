import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TaskDetail from '../components/TaskDetail';
import { TaskService } from '../services/taskService';
import { Task, TaskStatus, SmartSummaryResponse, SmartEstimateResponse, SmartRewriteResponse } from '../types/task';

// Mock the TaskService
jest.mock('../services/taskService');
const mockTaskService = TaskService as jest.Mocked<typeof TaskService>;

describe('AI Tools Integration', () => {
    
    const mockTask: Task = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        title: 'Implement User Authentication',
        description: 'Create a secure login system for the application',
        status: TaskStatus.IN_PROGRESS,
        estimate: 8,
        assignee: 1,
        reporter: 2,
        assignee_detail: { id: 1, username: 'developer', first_name: 'Dev', last_name: 'User', display_name: 'Dev User' },
        reporter_detail: { id: 2, username: 'pm', first_name: 'Project', last_name: 'Manager', display_name: 'Project Manager' },
        tags: ['backend', 'security'],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-02T00:00:00Z'
    };

    beforeEach(() => {
        jest.clearAllMocks();
        // Mock the task fetch
        mockTaskService.getTask.mockResolvedValue(mockTask);
    });

    describe('Complete AI Tools Workflow', () => {
        it('should handle complete workflow of all AI tools', async () => {
            // Mock AI tool responses
            const mockSummary: SmartSummaryResponse = {
                summary: 'This authentication task has been in progress for 1 day with 5 activities recorded. Current status shows active development with security considerations being addressed.'
            };

            const mockEstimate: SmartEstimateResponse = {
                suggested_points: 8,
                confidence: 0.85,
                similar_task_ids: [
                    '456e7890-e89b-12d3-a456-426614174001',
                    '789e0123-e89b-12d3-a456-426614174002'
                ],
                rationale: 'Based on 2 similar authentication tasks with same assignee. High confidence due to matching tags and similar complexity.'
            };

            const mockRewrite: SmartRewriteResponse = {
                title: 'Enhanced: Implement Secure User Authentication System with Multi-Factor Support',
                user_story: `As a user, I want to securely authenticate into the application so that my account and data are protected.

Acceptance Criteria:
- Users can register with email and strong password
- Users can log in with valid credentials
- Multi-factor authentication is supported
- Password reset functionality is available
- Session management prevents unauthorized access
- Failed login attempts are tracked and limited`
            };

            mockTaskService.startSmartSummary.mockResolvedValue({
                operation_id: '123e4567-e89b-12d3-a456-426614174000',
                status: 'pending',
                sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
            });
            mockTaskService.getSmartEstimate.mockResolvedValue(mockEstimate);
            mockTaskService.getSmartRewrite.mockResolvedValue(mockRewrite);

            render(<TaskDetail taskId={mockTask.id} />);

            // Wait for task to load
            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            // Test Smart Summary
            const summaryButton = screen.getByText('Smart Summary');
            await userEvent.click(summaryButton);

            await waitFor(() => {
                expect(screen.getByText(mockSummary.summary)).toBeInTheDocument();
            });

            // Test Smart Estimate
            const estimateButton = screen.getByText('Smart Estimate');
            await userEvent.click(estimateButton);

            await waitFor(() => {
                expect(screen.getByText('8 Points')).toBeInTheDocument();
                expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
                expect(screen.getByText('Similar Tasks (2):')).toBeInTheDocument();
                expect(screen.getByText('Task 456e7890...')).toBeInTheDocument();
                expect(screen.getByText('Task 789e0123...')).toBeInTheDocument();
            });

            // Test Smart Rewrite
            const rewriteButton = screen.getByText('Smart Rewrite');
            await userEvent.click(rewriteButton);

            await waitFor(() => {
                expect(screen.getByText(mockRewrite.title)).toBeInTheDocument();
                expect(screen.getByText(/As a user, I want to securely authenticate/)).toBeInTheDocument();
                expect(screen.getByText(/Multi-factor authentication is supported/)).toBeInTheDocument();
            });

            // Verify all API calls were made
            expect(mockTaskService.getTask).toHaveBeenCalledWith(mockTask.id);
            expect(mockTaskService.getSmartSummary).toHaveBeenCalledWith(mockTask.id);
            expect(mockTaskService.getSmartEstimate).toHaveBeenCalledWith(mockTask.id);
            expect(mockTaskService.getSmartRewrite).toHaveBeenCalledWith(mockTask.id);
        });

        it('should handle mixed success and error states', async () => {
            // Mock mixed responses
            const mockSummary: SmartSummaryResponse = {
                summary: 'Task summary generated successfully.'
            };

            mockTaskService.startSmartSummary.mockResolvedValue({
                operation_id: '123e4567-e89b-12d3-a456-426614174000',
                status: 'pending',
                sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
            });
            mockTaskService.getSmartEstimate.mockRejectedValue(new Error('Failed to calculate smart estimate'));
            mockTaskService.getSmartRewrite.mockRejectedValue(new Error('Task not found for rewrite generation'));

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            // Test successful summary
            await userEvent.click(screen.getByText('Smart Summary'));
            await waitFor(() => {
                expect(screen.getByText('Task summary generated successfully.')).toBeInTheDocument();
            });

            // Test failed estimate
            await userEvent.click(screen.getByText('Smart Estimate'));
            await waitFor(() => {
                expect(screen.getByText('Failed to calculate smart estimate')).toBeInTheDocument();
            });

            // Test failed rewrite
            await userEvent.click(screen.getByText('Smart Rewrite'));
            await waitFor(() => {
                expect(screen.getByText('Task not found for rewrite generation')).toBeInTheDocument();
            });
        });

        it('should handle concurrent AI tool requests', async () => {
            // Mock responses with delays to simulate concurrent requests
            const mockSummary: SmartSummaryResponse = { summary: 'Summary result' };
            const mockEstimate: SmartEstimateResponse = {
                suggested_points: 5,
                confidence: 0.7,
                similar_task_ids: [],
                rationale: 'Estimate result'
            };

            mockTaskService.startSmartSummary.mockImplementation(() => 
                new Promise(resolve => {
                    setTimeout(() => resolve({
                        operation_id: '123e4567-e89b-12d3-a456-426614174000',
                        status: 'pending',
                        sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
                    }), 100);
                })
            );

            mockTaskService.getSmartEstimate.mockImplementation(() => 
                new Promise(resolve => {
                    setTimeout(() => resolve(mockEstimate), 150);
                })
            );

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            // Click both buttons quickly
            await userEvent.click(screen.getByText('Smart Summary'));
            await userEvent.click(screen.getByText('Smart Estimate'));

            // Both should show loading states
            expect(screen.getByText('Generating...')).toBeInTheDocument();
            expect(screen.getByText('Calculating...')).toBeInTheDocument();

            // Wait for both to complete
            await waitFor(() => {
                expect(screen.getByText('Summary result')).toBeInTheDocument();
            });

            await waitFor(() => {
                expect(screen.getByText('5 Points')).toBeInTheDocument();
            });
        });

        it('should handle authentication errors properly', async () => {
            mockTaskService.startSmartSummary.mockRejectedValue(new Error('Failed to generate smart summary'));

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Smart Summary'));

            await waitFor(() => {
                expect(screen.getByText('Failed to generate smart summary')).toBeInTheDocument();
            });
        });

        it('should maintain button states correctly during operations', async () => {
            mockTaskService.startSmartSummary.mockImplementation(() => 
                new Promise(resolve => {
                    setTimeout(() => resolve({
                        operation_id: '123e4567-e89b-12d3-a456-426614174000',
                        status: 'pending',
                        sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
                    }), 200);
                })
            );

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            const summaryButton = screen.getByText('Smart Summary');
            const estimateButton = screen.getByText('Smart Estimate');
            const rewriteButton = screen.getByText('Smart Rewrite');

            // Initially all buttons should be enabled
            expect(summaryButton).not.toBeDisabled();
            expect(estimateButton).not.toBeDisabled();
            expect(rewriteButton).not.toBeDisabled();

            // Click summary button
            await userEvent.click(summaryButton);

            // Summary button should be disabled, others should remain enabled
            expect(summaryButton).toBeDisabled();
            expect(estimateButton).not.toBeDisabled();
            expect(rewriteButton).not.toBeDisabled();

            // Wait for completion
            await waitFor(() => {
                expect(screen.getByText('Test summary')).toBeInTheDocument();
            });

            // All buttons should be enabled again
            expect(summaryButton).not.toBeDisabled();
            expect(estimateButton).not.toBeDisabled();
            expect(rewriteButton).not.toBeDisabled();
        });
    });

    describe('Similar Tasks Links Integration', () => {
        it('should create working links to similar tasks', async () => {
            const mockEstimate: SmartEstimateResponse = {
                suggested_points: 5,
                confidence: 0.8,
                similar_task_ids: [
                    '456e7890-e89b-12d3-a456-426614174001',
                    '789e0123-e89b-12d3-a456-426614174002',
                    'abc1234d-e89b-12d3-a456-426614174003'
                ],
                rationale: 'Based on similar authentication tasks'
            };

            mockTaskService.getSmartEstimate.mockResolvedValue(mockEstimate);

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Smart Estimate'));

            await waitFor(() => {
                expect(screen.getByText('Similar Tasks (3):')).toBeInTheDocument();
            });

            // Check that all links are present and correctly formatted
            const links = screen.getAllByRole('link');
            expect(links).toHaveLength(3);

            expect(links[0]).toHaveAttribute('href', '/tasks/456e7890-e89b-12d3-a456-426614174001');
            expect(links[0]).toHaveTextContent('Task 456e7890...');

            expect(links[1]).toHaveAttribute('href', '/tasks/789e0123-e89b-12d3-a456-426614174002');
            expect(links[1]).toHaveTextContent('Task 789e0123...');

            expect(links[2]).toHaveAttribute('href', '/tasks/abc1234d-e89b-12d3-a456-426614174003');
            expect(links[2]).toHaveTextContent('Task abc1234d...');

            // Check numbered chips
            expect(screen.getByText('#1')).toBeInTheDocument();
            expect(screen.getByText('#2')).toBeInTheDocument();
            expect(screen.getByText('#3')).toBeInTheDocument();
        });
    });

    describe('Error Recovery', () => {
        it('should allow retry after error', async () => {
            // First call fails, second succeeds
            mockTaskService.startSmartSummary
                .mockRejectedValueOnce(new Error('Failed to generate smart summary'))
                .mockResolvedValueOnce({
                    operation_id: '123e4567-e89b-12d3-a456-426614174000',
                    status: 'pending',
                    sse_url: '/api/ai-operations/123e4567-e89b-12d3-a456-426614174000/stream/'
                });

            render(<TaskDetail taskId={mockTask.id} />);

            await waitFor(() => {
                expect(screen.getByText('Implement User Authentication')).toBeInTheDocument();
            });

            // First attempt fails
            await userEvent.click(screen.getByText('Smart Summary'));
            await waitFor(() => {
                expect(screen.getByText('Failed to generate smart summary')).toBeInTheDocument();
            });

            // Second attempt succeeds
            await userEvent.click(screen.getByText('Smart Summary'));
            await waitFor(() => {
                expect(screen.getByText('Retry successful')).toBeInTheDocument();
            });
        });
    });
});