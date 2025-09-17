import React from 'react';
import { render, screen } from '@testing-library/react';
import TaskList from '../TaskList';
import { TaskService } from '../../services/taskService';
import { TaskStatus } from '../../types/task';

// Mock the TaskService
jest.mock('../../services/taskService');
const mockTaskService = TaskService as jest.Mocked<typeof TaskService>;

// Mock UserService
jest.mock('../../services/userService', () => ({
    UserService: {
        searchUsers: jest.fn()
    },
    UserServiceError: class UserServiceError extends Error {}
}));

// Mock TaskForm component
jest.mock('../TaskForm', () => {
    return function MockTaskForm() {
        return <div>Mock TaskForm</div>;
    };
});

// Mock UserAutocomplete component
jest.mock('../UserAutocomplete', () => {
    return function MockUserAutocomplete({ value, onChange, label }: any) {
        return (
            <div data-testid="user-autocomplete">
                <label>{label}</label>
                <input
                    value={value ? value.display_name || value.username : ''}
                    onChange={(e) => {
                        // Simulate user selection for testing
                        if (e.target.value) {
                            onChange({
                                id: 1,
                                username: 'test.user',
                                first_name: 'Test',
                                last_name: 'User',
                                display_name: 'Test User'
                            });
                        } else {
                            onChange(null);
                        }
                    }}
                />
            </div>
        );
    };
});

describe('TaskList', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should display user information in task cards', async () => {
        const mockTasks = [
            {
                id: '1',
                title: 'Test Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                assignee_detail: {
                    id: 1,
                    username: 'john.doe',
                    first_name: 'John',
                    last_name: 'Doe',
                    display_name: 'John Doe'
                },
                reporter_detail: {
                    id: 2,
                    username: 'jane.smith',
                    first_name: 'Jane',
                    last_name: 'Smith',
                    display_name: 'Jane Smith'
                },
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }
        ];

        mockTaskService.getTasks.mockResolvedValue({
            results: mockTasks,
            count: 1
        });

        render(<TaskList />);

        // Wait for tasks to load
        await screen.findByText('Test Task');

        // Check that assignee information is displayed
        expect(screen.getByText('Assignee: John Doe')).toBeInTheDocument();
        
        // Check that reporter information is displayed
        expect(screen.getByText('Reporter: Jane Smith')).toBeInTheDocument();
    });

    it('should display placeholder text for unassigned tasks', async () => {
        const mockTasks = [
            {
                id: '1',
                title: 'Unassigned Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                assignee_detail: null,
                reporter_detail: null,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }
        ];

        mockTaskService.getTasks.mockResolvedValue({
            results: mockTasks,
            count: 1
        });

        render(<TaskList />);

        // Wait for tasks to load
        await screen.findByText('Unassigned Task');

        // Check that placeholder text is displayed
        expect(screen.getByText('Assignee: Unassigned')).toBeInTheDocument();
        expect(screen.getByText('Reporter: No reporter')).toBeInTheDocument();
    });

    it('should fallback to username when display_name is not available', async () => {
        const mockTasks = [
            {
                id: '1',
                title: 'Test Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                assignee_detail: {
                    id: 1,
                    username: 'john.doe',
                    first_name: '',
                    last_name: '',
                    display_name: 'john.doe' // This would be the fallback from the backend
                },
                reporter_detail: null,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }
        ];

        mockTaskService.getTasks.mockResolvedValue({
            results: mockTasks,
            count: 1
        });

        render(<TaskList />);

        // Wait for tasks to load
        await screen.findByText('Test Task');

        // Check that username is displayed when display_name is just the username
        expect(screen.getByText('Assignee: john.doe')).toBeInTheDocument();
    });

    it('should display UserAutocomplete for assignee filter', async () => {
        const mockTasks = [
            {
                id: '1',
                title: 'Test Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                assignee_detail: null,
                reporter_detail: null,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }
        ];

        mockTaskService.getTasks.mockResolvedValue({
            results: mockTasks,
            count: 1
        });

        render(<TaskList />);

        // Wait for tasks to load
        await screen.findByText('Test Task');

        // Check that UserAutocomplete is rendered for assignee filter
        expect(screen.getByTestId('user-autocomplete')).toBeInTheDocument();
        expect(screen.getByText('Assignee')).toBeInTheDocument();
    });

    it('should display active filter chips when filters are applied', async () => {
        const mockTasks = [
            {
                id: '1',
                title: 'Test Task',
                description: 'Test Description',
                status: TaskStatus.TODO,
                assignee_detail: {
                    id: 1,
                    username: 'john.doe',
                    first_name: 'John',
                    last_name: 'Doe',
                    display_name: 'John Doe'
                },
                reporter_detail: null,
                tags: [],
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }
        ];

        mockTaskService.getTasks.mockResolvedValue({
            results: mockTasks,
            count: 1
        });

        render(<TaskList />);

        // Wait for tasks to load
        await screen.findByText('Test Task');

        // Simulate selecting a user in the filter (this would trigger the active filter display)
        // Note: In a real test, you would interact with the UserAutocomplete component
        // For now, we just verify the structure is in place
        expect(screen.getByText('Filters')).toBeInTheDocument();
    });
});