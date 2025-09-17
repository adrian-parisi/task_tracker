export interface Task {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    estimate?: number;
    assignee?: User;
    reporter?: User;
    tags: Tag[];
    created_at: string;
    updated_at: string;
}

export enum TaskStatus {
    TODO = 'TODO',
    IN_PROGRESS = 'IN_PROGRESS',
    BLOCKED = 'BLOCKED',
    DONE = 'DONE'
}

export interface User {
    id: number;
    username: string;
    email: string;
}

export interface Tag {
    id: number;
    name: string;
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