import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TaskDetail from '../TaskDetail';
import { TaskService } from '../../services/taskService';
import { Task, TaskStatus, SmartSummaryResponse, SmartEstimateResponse, SmartRewriteResponse } from '../../types/task';

// Mock the TaskService
jest.mock('../../services/taskService');
const mockTaskService = TaskService as jest.Mocked<typeof TaskService>;

// Mock the display components
jest.mock('../SummaryDisplay', () => ({
    __esModule: true,
    default: function MockSummaryDisplay({ summary, loading, error }: any) {
        if (loading) return React.createElement('div', { 'data-testid': 'summary-loading' }, 'Loading summary...');
        if (error) return React.createElement('div', { 'data-testid': 'summary-error' }, error);
        if (summary) return React.createElement('div', { 'data-testid': 'summary-display' }, summary);
        return null;
    }
}));

jest.mock('../EstimateDisplay', () => ({
    __esModule: true,
    default: function MockEstimateDisplay({ estimate, loading, error }: any) {
        if (loading) return React.createElement('div', { 'data-testid': 'estimate-loading' }, 'Loading estimate...');
        if (error) return React.createElement('div', { 'data-testid': 'estimate-error' }, error);
        if (estimate) return React.createElement('div', { 'data-testid': 'estimate-display' }, JSON.stringify(estimate));
        return null;
    }
}));

jest.mock('../RewriteDisplay', () => ({
    __esModule: true,
    default: function MockRewriteDisplay({ rewrite, loading, error }: any) {
        if (loading) return React.createElement('div', { 'data-testid': 'rewrite-loading' }, 'Loading rewrite...');
        if (error) return React.createElement('div', { 'data-testid': 'rewrite-error' }, error);
        if (rewrite) return React.createElement('div', { 'data-testid': 'rewrite-display' }, JSON.stringify(rewrite));
        return null;
    }
}));

describe('TaskDetail', () => {
    const mockTask: Task = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        title: 'Test Task',
        description: 'Test task description',
        status: TaskStatus.TODO,
        estimate: 5,
        assignee: 1,
        reporter: 2,
        assignee_detail: { id: 1, username: 'testuser', first_name: 'Test', last_name: 'User', display_name: 'Test User' },
        reporter_detail: { id: 2, username: 'reporter', first_name: 'Reporter', last_name: 'User', display_name: 'Reporter User' },
        tags: [
            { id: 1, name: 'frontend' },
            { id: 2, name: 'urgent' }
        ],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Task Loading', () => {
        it('should show loading state initially', () => {
            mockTaskService.getTask.mockImplementation(() => new Promise(() => { }));

            render(<TaskDetail taskId="123" />);

            expect(screen.getByRole('progressbar')).toBeInTheDocument();
        });

        it('should display task details after loading', async () => {
            mockTaskService.getTask.mockResolvedValue(mockTask);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            expect(screen.getByText('Test task description')).toBeInTheDocument();
            expect(screen.getByText('TODO')).toBeInTheDocument();
            expect(screen.getByText('Estimate: 5 points')).toBeInTheDocument();
            expect(screen.getByText('Assignee: testuser')).toBeInTheDocument();
            expect(screen.getByText('Reporter: reporter')).toBeInTheDocument();
            expect(screen.getByText('frontend')).toBeInTheDocument();
            expect(screen.getByText('urgent')).toBeInTheDocument();
        });

        it('should show error message when task loading fails', async () => {
            mockTaskService.getTask.mockRejectedValue(new Error('Failed to load task'));

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Failed to load task')).toBeInTheDocument();
            });
        });

        it('should show task not found when task is null', async () => {
            mockTaskService.getTask.mockResolvedValue(null as any);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Task not found')).toBeInTheDocument();
            });
        });
    });

    describe('AI Tool Interactions', () => {
        beforeEach(async () => {
            mockTaskService.getTask.mockResolvedValue(mockTask);
            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });
        });

        describe('Smart Summary', () => {
            it('should call smart summary API when button is clicked', async () => {
                const mockSummary: SmartSummaryResponse = {
                    summary: 'This task has been created and is in TODO status.'
                };
                mockTaskService.getSmartSummary.mockResolvedValue(mockSummary);

                const summaryButton = screen.getByText('Smart Summary');
                await userEvent.click(summaryButton);

                expect(mockTaskService.getSmartSummary).toHaveBeenCalledWith('123');

                await waitFor(() => {
                    expect(screen.getByTestId('summary-display')).toBeInTheDocument();
                });
            });

            it('should show loading state during summary generation', async () => {
                mockTaskService.getSmartSummary.mockImplementation(() => new Promise(() => { }));

                const summaryButton = screen.getByText('Smart Summary');
                await userEvent.click(summaryButton);

                expect(screen.getByText('Generating...')).toBeInTheDocument();
                expect(summaryButton).toBeDisabled();
                expect(screen.getByTestId('summary-loading')).toBeInTheDocument();
            });

            it('should show error message when summary generation fails', async () => {
                mockTaskService.getSmartSummary.mockRejectedValue(new Error('Failed to generate summary'));

                const summaryButton = screen.getByText('Smart Summary');
                await userEvent.click(summaryButton);

                await waitFor(() => {
                    expect(screen.getByTestId('summary-error')).toBeInTheDocument();
                });
            });
        });

        describe('Smart Estimate', () => {
            it('should call smart estimate API when button is clicked', async () => {
                const mockEstimate: SmartEstimateResponse = {
                    suggested_points: 3,
                    confidence: 0.75,
                    similar_task_ids: ['456e7890-e89b-12d3-a456-426614174001'],
                    rationale: 'Based on similar tasks'
                };
                mockTaskService.getSmartEstimate.mockResolvedValue(mockEstimate);

                const estimateButton = screen.getByText('Smart Estimate');
                await userEvent.click(estimateButton);

                expect(mockTaskService.getSmartEstimate).toHaveBeenCalledWith('123');

                await waitFor(() => {
                    expect(screen.getByTestId('estimate-display')).toBeInTheDocument();
                });
            });

            it('should show loading state during estimate calculation', async () => {
                mockTaskService.getSmartEstimate.mockImplementation(() => new Promise(() => { }));

                const estimateButton = screen.getByText('Smart Estimate');
                await userEvent.click(estimateButton);

                expect(screen.getByText('Calculating...')).toBeInTheDocument();
                expect(estimateButton).toBeDisabled();
                expect(screen.getByTestId('estimate-loading')).toBeInTheDocument();
            });

            it('should show error message when estimate calculation fails', async () => {
                mockTaskService.getSmartEstimate.mockRejectedValue(new Error('Failed to calculate estimate'));

                const estimateButton = screen.getByText('Smart Estimate');
                await userEvent.click(estimateButton);

                await waitFor(() => {
                    expect(screen.getByTestId('estimate-error')).toBeInTheDocument();
                });
            });
        });

        describe('Smart Rewrite', () => {
            it('should call smart rewrite API when button is clicked', async () => {
                const mockRewrite: SmartRewriteResponse = {
                    title: 'Enhanced Task Title',
                    user_story: 'As a user, I want to complete this task so that I can achieve my goal.'
                };
                mockTaskService.getSmartRewrite.mockResolvedValue(mockRewrite);

                const rewriteButton = screen.getByText('Smart Rewrite');
                await userEvent.click(rewriteButton);

                expect(mockTaskService.getSmartRewrite).toHaveBeenCalledWith('123');

                await waitFor(() => {
                    expect(screen.getByTestId('rewrite-display')).toBeInTheDocument();
                });
            });

            it('should show loading state during rewrite generation', async () => {
                mockTaskService.getSmartRewrite.mockImplementation(() => new Promise(() => { }));

                const rewriteButton = screen.getByText('Smart Rewrite');
                await userEvent.click(rewriteButton);

                expect(screen.getByText('Rewriting...')).toBeInTheDocument();
                expect(rewriteButton).toBeDisabled();
                expect(screen.getByTestId('rewrite-loading')).toBeInTheDocument();
            });

            it('should show error message when rewrite generation fails', async () => {
                mockTaskService.getSmartRewrite.mockRejectedValue(new Error('Failed to generate rewrite'));

                const rewriteButton = screen.getByText('Smart Rewrite');
                await userEvent.click(rewriteButton);

                await waitFor(() => {
                    expect(screen.getByTestId('rewrite-error')).toBeInTheDocument();
                });
            });
        });
    });

    describe('Callback Functions', () => {
        it('should call onBack when back button is clicked', async () => {
            const mockOnBack = jest.fn();
            mockTaskService.getTask.mockResolvedValue(mockTask);

            render(<TaskDetail taskId="123" onBack={mockOnBack} />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            const backButton = screen.getByLabelText('ArrowBack');
            await userEvent.click(backButton);

            expect(mockOnBack).toHaveBeenCalled();
        });

        it('should call onEdit when edit button is clicked', async () => {
            const mockOnEdit = jest.fn();
            mockTaskService.getTask.mockResolvedValue(mockTask);

            render(<TaskDetail taskId="123" onEdit={mockOnEdit} />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            const editButton = screen.getByText('Edit');
            await userEvent.click(editButton);

            expect(mockOnEdit).toHaveBeenCalledWith(mockTask);
        });
    });

    describe('Status Display', () => {
        it('should display correct status colors', async () => {
            const taskWithInProgress = { ...mockTask, status: TaskStatus.IN_PROGRESS };
            mockTaskService.getTask.mockResolvedValue(taskWithInProgress);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
            });
        });
    });

    describe('Conditional Rendering', () => {
        it('should not show estimate when not provided', async () => {
            const taskWithoutEstimate = { ...mockTask, estimate: undefined };
            mockTaskService.getTask.mockResolvedValue(taskWithoutEstimate);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            expect(screen.queryByText(/Estimate:/)).not.toBeInTheDocument();
        });

        it('should not show assignee when not provided', async () => {
            const taskWithoutAssignee = { ...mockTask, assignee: undefined };
            mockTaskService.getTask.mockResolvedValue(taskWithoutAssignee);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            expect(screen.queryByText(/Assignee:/)).not.toBeInTheDocument();
        });

        it('should show no description message when description is empty', async () => {
            const taskWithoutDescription = { ...mockTask, description: '' };
            mockTaskService.getTask.mockResolvedValue(taskWithoutDescription);

            render(<TaskDetail taskId="123" />);

            await waitFor(() => {
                expect(screen.getByText('Test Task')).toBeInTheDocument();
            });

            expect(screen.getByText('No description provided')).toBeInTheDocument();
        });
    });
});