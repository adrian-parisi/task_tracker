export interface Task {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    estimate?: number;
    project?: string; // Project ID for write operations
    project_detail?: Project | null; // Full project object for read operations
    assignee?: number; // User ID for write operations
    assignee_detail?: TaskUser | null; // Full user object for read operations
    reporter?: number; // User ID for write operations
    reporter_detail?: TaskUser | null; // Full user object for read operations
    tags: string[];
    created_at: string;
    updated_at: string;
}

export enum TaskStatus {
    TODO = 'TODO',
    IN_PROGRESS = 'IN_PROGRESS',
    BLOCKED = 'BLOCKED',
    DONE = 'DONE'
}

// User interface for user management (matches backend User model)
export interface User {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    display_name: string;
}

// TaskUser is an alias for User to maintain backward compatibility
export type TaskUser = User;


export interface Project {
    id: string;
    code: string;
    name: string;
    description?: string;
    is_active: boolean;
}

export interface SmartSummaryResponse {
    summary: string;
}

export interface SmartEstimateResponse {
    suggested_points: number;
    confidence: number;
    similar_task_ids: string[];
    rationale: string;
}

export interface SmartRewriteResponse {
    title: string;
    user_story: string;
}

export interface TaskListResponse {
    results: Task[];
    count: number;
    next?: string;
    previous?: string;
}