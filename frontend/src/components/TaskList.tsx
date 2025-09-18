import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Chip,
    Grid,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Alert,
    CircularProgress,
    Collapse,
    Paper
} from '@mui/material';
import {
    Add,
    Edit,
    Delete,
    FilterList,
    AutoAwesome,
    EditNote,
    Person,
    Flag,
    ExpandMore,
    ExpandLess
} from '@mui/icons-material';
import { Task, TaskStatus, SmartRewriteResponse, SmartSummaryResponse } from '../types/task';
import { TaskService } from '../services/taskService';
import { sseService } from '../services/sseService';
import { User } from '../types/task';
import TaskForm from './TaskForm';
import UserAutocomplete from './UserAutocomplete';

const TaskList: React.FC = () => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    const [showTaskForm, setShowTaskForm] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
    const [showSummaryDialog, setShowSummaryDialog] = useState(false);
    const [summaryTask, setSummaryTask] = useState<Task | null>(null);
    const [summary, setSummary] = useState<string>('');
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [summaryError, setSummaryError] = useState<string>('');
    const [showRewriteDialog, setShowRewriteDialog] = useState(false);
    const [rewriteTask, setRewriteTask] = useState<Task | null>(null);
    const [rewrite, setRewrite] = useState<SmartRewriteResponse | null>(null);
    const [rewriteLoading, setRewriteLoading] = useState(false);
    const [rewriteError, setRewriteError] = useState<string>('');
    
    // AI operations state per task
    const [taskAiOperations, setTaskAiOperations] = useState<Record<string, {
        summary: {
            loading: boolean;
            result: SmartSummaryResponse | null;
            error: string;
            expanded: boolean;
        };
        rewrite: {
            loading: boolean;
            result: SmartRewriteResponse | null;
            error: string;
            expanded: boolean;
        };
    }>>({});
    
    const [filters, setFilters] = useState({
        status: '',
        assignee: null as User | null
    });

    useEffect(() => {
        loadTasks();
    }, [filters]);

    // Cleanup SSE connections on unmount
    useEffect(() => {
        return () => {
            sseService.disconnect();
        };
    }, []);

    const loadTasks = async () => {
        try {
            setLoading(true);
            setError('');
            const apiFilters = {
                status: filters.status || undefined,
                assignee: filters.assignee?.id || undefined
            };
            const response = await TaskService.getTasks(apiFilters);
            setTasks(response.results);
        } catch (err) {
            setError('Failed to load tasks');
            console.error('Failed to load tasks:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTask = () => {
        setSelectedTask(null);
        setShowTaskForm(true);
    };

    const handleEditTask = (task: Task) => {
        setSelectedTask(task);
        setShowTaskForm(true);
    };

    const handleDeleteTask = (task: Task) => {
        setTaskToDelete(task);
        setShowDeleteDialog(true);
    };

    const confirmDeleteTask = async () => {
        if (!taskToDelete) return;

        try {
            await TaskService.deleteTask(taskToDelete.id);
            setTasks(tasks.filter(task => task.id !== taskToDelete.id));
            setShowDeleteDialog(false);
            setTaskToDelete(null);
        } catch (err) {
            setError('Failed to delete task');
            console.error('Failed to delete task:', err);
        }
    };

    const handleSmartSummary = async (task: Task) => {
        // Initialize AI operation state for this task
        setTaskAiOperations(prev => ({
            ...prev,
            [task.id]: {
                ...prev[task.id],
                summary: {
                    loading: true,
                    result: null,
                    error: '',
                    expanded: true
                }
            }
        }));

        try {
            const operation = await TaskService.startSmartSummary(task.id);
            console.log('Summary operation started:', operation.operation_id);

            // Connect to SSE for real-time updates
            sseService.connect(
                operation.operation_id,
                (data) => {
                    console.log('TaskList received SSE data:', data);
                    if (data.status === 'completed') {
                        console.log('Updating task with completed summary:', data.result);
                        setTaskAiOperations(prev => ({
                            ...prev,
                            [task.id]: {
                                ...prev[task.id],
                                summary: {
                                    loading: false,
                                    result: data.result,
                                    error: '',
                                    expanded: true
                                }
                            }
                        }));
                    } else if (data.status === 'failed') {
                        console.log('Updating task with failed summary:', data.error);
                        setTaskAiOperations(prev => ({
                            ...prev,
                            [task.id]: {
                                ...prev[task.id],
                                summary: {
                                    loading: false,
                                    result: null,
                                    error: data.error || 'Summary generation failed',
                                    expanded: true
                                }
                            }
                        }));
                    }
                },
                (error) => {
                    setTaskAiOperations(prev => ({
                        ...prev,
                        [task.id]: {
                            ...prev[task.id],
                            summary: {
                                loading: false,
                                result: null,
                                error: 'Connection lost. Please try again.',
                                expanded: true
                            }
                        }
                    }));
                }
            );
        } catch (err) {
            setTaskAiOperations(prev => ({
                ...prev,
                [task.id]: {
                    ...prev[task.id],
                    summary: {
                        loading: false,
                        result: null,
                        error: 'Failed to start summary generation',
                        expanded: true
                    }
                }
            }));
            console.error('Failed to start summary generation:', err);
        }
    };

    const handleSmartRewrite = async (task: Task) => {
        // Initialize AI operation state for this task
        setTaskAiOperations(prev => ({
            ...prev,
            [task.id]: {
                ...prev[task.id],
                rewrite: {
                    loading: true,
                    result: null,
                    error: '',
                    expanded: true
                }
            }
        }));

        try {
            const rewriteResult = await TaskService.getSmartRewrite(task.id);
            console.log('Rewrite completed:', rewriteResult);

            setTaskAiOperations(prev => ({
                ...prev,
                [task.id]: {
                    ...prev[task.id],
                    rewrite: {
                        loading: false,
                        result: rewriteResult,
                        error: '',
                        expanded: true
                    }
                }
            }));
        } catch (err) {
            setTaskAiOperations(prev => ({
                ...prev,
                [task.id]: {
                    ...prev[task.id],
                    rewrite: {
                        loading: false,
                        result: null,
                        error: 'Failed to get rewrite',
                        expanded: true
                    }
                }
            }));
            console.error('Failed to get rewrite:', err);
        }
    };

    const handleTaskSaved = (savedTask: Task) => {
        if (selectedTask) {
            // Update existing task
            setTasks(tasks.map(task =>
                task.id === savedTask.id ? savedTask : task
            ));
        } else {
            // Add new task
            setTasks([savedTask, ...tasks]);
        }
        setShowTaskForm(false);
        setSelectedTask(null);
    };

    const toggleAiResult = (taskId: string, operationType: 'summary' | 'rewrite') => {
        setTaskAiOperations(prev => ({
            ...prev,
            [taskId]: {
                ...prev[taskId],
                [operationType]: {
                    ...prev[taskId]?.[operationType],
                    expanded: !prev[taskId]?.[operationType]?.expanded
                }
            }
        }));
    };

    const getStatusColor = (status: TaskStatus) => {
        switch (status) {
            case TaskStatus.TODO:
                return 'default';
            case TaskStatus.IN_PROGRESS:
                return 'primary';
            case TaskStatus.BLOCKED:
                return 'error';
            case TaskStatus.DONE:
                return 'success';
            default:
                return 'default';
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    Tasks
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleCreateTask}
                >
                    Create Task
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Filters */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <FilterList />
                        <Typography variant="h6">Filters</Typography>
                    </Box>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth size="small">
                                <InputLabel>Status</InputLabel>
                                <Select
                                    value={filters.status}
                                    label="Status"
                                    onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                                >
                                    <MenuItem value="">All</MenuItem>
                                    <MenuItem value="TODO">To Do</MenuItem>
                                    <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
                                    <MenuItem value="BLOCKED">Blocked</MenuItem>
                                    <MenuItem value="DONE">Done</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <UserAutocomplete
                                value={filters.assignee}
                                onChange={(user) => setFilters({ ...filters, assignee: user })}
                                label="Assignee"
                                placeholder="Filter by assignee..."
                            />
                        </Grid>
                    </Grid>
                    
                    {/* Active Filters Display */}
                    {(filters.status || filters.assignee) && (
                        <Box mt={2}>
                            <Typography variant="body2" color="text.secondary" mb={1}>
                                Active Filters:
                            </Typography>
                            <Box display="flex" gap={1} flexWrap="wrap">
                                {filters.status && (
                                    <Chip
                                        label={`Status: ${filters.status.replace('_', ' ')}`}
                                        size="small"
                                        onDelete={() => setFilters({ ...filters, status: '' })}
                                        color="primary"
                                        variant="outlined"
                                    />
                                )}
                                {filters.assignee && (
                                    <Chip
                                        label={`Assignee: ${filters.assignee.display_name || filters.assignee.username}`}
                                        size="small"
                                        onDelete={() => setFilters({ ...filters, assignee: null })}
                                        color="primary"
                                        variant="outlined"
                                    />
                                )}
                            </Box>
                        </Box>
                    )}
                </CardContent>
            </Card>

            {/* Task List */}
            <Grid container spacing={2}>
                {tasks.map((task) => (
                    <Grid item xs={12} md={6} lg={4} key={task.id}>
                        <Card>
                            <CardContent>
                                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                                    <Typography variant="h6" component="h2" noWrap>
                                        {task.title}
                                    </Typography>
                                    <Box>
                                        <IconButton
                                            size="small"
                                            onClick={() => handleSmartSummary(task)}
                                            title="Smart Summary"
                                        >
                                            <AutoAwesome />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            onClick={() => handleSmartRewrite(task)}
                                            title="Smart Rewrite"
                                        >
                                            <EditNote />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => handleEditTask(task)}>
                                            <Edit />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => handleDeleteTask(task)}>
                                            <Delete />
                                        </IconButton>
                                    </Box>
                                </Box>

                                <Typography variant="body2" color="text.secondary" mb={2} noWrap>
                                    {task.description || 'No description'}
                                </Typography>

                                <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                                    <Chip
                                        label={task.status.replace('_', ' ')}
                                        color={getStatusColor(task.status)}
                                        size="small"
                                    />
                                    {task.estimate && (
                                        <Chip
                                            label={`${task.estimate} pts`}
                                            variant="outlined"
                                            size="small"
                                        />
                                    )}
                                </Box>

                                {/* Tags */}
                                {task.tags && task.tags.length > 0 && (
                                    <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                                        {task.tags.map((tag, index) => (
                                            <Chip
                                                key={index}
                                                label={tag}
                                                variant="outlined"
                                                size="small"
                                                color="secondary"
                                            />
                                        ))}
                                    </Box>
                                )}

                                {/* Assignee Information */}
                                <Box display="flex" alignItems="center" gap={1} mb={1}>
                                    <Person fontSize="small" color="action" />
                                    <Typography variant="body2" color="text.secondary">
                                        Assignee: {task.assignee_detail 
                                            ? (task.assignee_detail.display_name || task.assignee_detail.username)
                                            : 'Unassigned'
                                        }
                                    </Typography>
                                </Box>

                                {/* Reporter Information */}
                                <Box display="flex" alignItems="center" gap={1}>
                                    <Flag fontSize="small" color="action" />
                                    <Typography variant="body2" color="text.secondary">
                                        Reporter: {task.reporter_detail 
                                            ? (task.reporter_detail.display_name || task.reporter_detail.username)
                                            : 'No reporter'
                                        }
                                    </Typography>
                                </Box>

                                {/* AI Operations Results */}
                                {taskAiOperations[task.id] && (
                                    <Box mt={2}>
                                        {/* Smart Summary */}
                                        {(taskAiOperations[task.id].summary?.loading || 
                                          taskAiOperations[task.id].summary?.result || 
                                          taskAiOperations[task.id].summary?.error) && (
                                            <Box mb={2}>
                                                <Box 
                                                    display="flex" 
                                                    alignItems="center" 
                                                    gap={1} 
                                                    sx={{ cursor: 'pointer' }}
                                                    onClick={() => toggleAiResult(task.id, 'summary')}
                                                >
                                                    <AutoAwesome fontSize="small" color="primary" />
                                                    <Typography variant="body2" fontWeight="medium">
                                                        Smart Summary
                                                    </Typography>
                                                    {taskAiOperations[task.id].summary?.loading && (
                                                        <CircularProgress size={16} />
                                                    )}
                                                    {taskAiOperations[task.id].summary?.expanded ? 
                                                        <ExpandLess fontSize="small" /> : 
                                                        <ExpandMore fontSize="small" />
                                                    }
                                                </Box>
                                                
                                                <Collapse in={taskAiOperations[task.id].summary?.expanded}>
                                                    <Paper 
                                                        elevation={1} 
                                                        sx={{ 
                                                            p: 2, 
                                                            mt: 1, 
                                                            bgcolor: 'grey.50',
                                                            border: '1px solid',
                                                            borderColor: 'grey.200'
                                                        }}
                                                    >
                                                        {taskAiOperations[task.id].summary?.loading && (
                                                            <Box display="flex" alignItems="center" gap={1}>
                                                                <CircularProgress size={16} />
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Generating summary...
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                        
                                                        {taskAiOperations[task.id].summary?.error && (
                                                            <Alert severity="error" sx={{ mb: 1 }}>
                                                                {taskAiOperations[task.id].summary.error}
                                                            </Alert>
                                                        )}
                                                        
                                                        {taskAiOperations[task.id].summary?.result && (
                                                            <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                                                                {taskAiOperations[task.id].summary?.result?.summary}
                                                            </Typography>
                                                        )}
                                                    </Paper>
                                                </Collapse>
                                            </Box>
                                        )}

                                        {/* Smart Rewrite */}
                                        {(taskAiOperations[task.id].rewrite?.loading || 
                                          taskAiOperations[task.id].rewrite?.result || 
                                          taskAiOperations[task.id].rewrite?.error) && (
                                            <Box>
                                                <Box 
                                                    display="flex" 
                                                    alignItems="center" 
                                                    gap={1} 
                                                    sx={{ cursor: 'pointer' }}
                                                    onClick={() => toggleAiResult(task.id, 'rewrite')}
                                                >
                                                    <EditNote fontSize="small" color="primary" />
                                                    <Typography variant="body2" fontWeight="medium">
                                                        Smart Rewrite
                                                    </Typography>
                                                    {taskAiOperations[task.id].rewrite?.loading && (
                                                        <CircularProgress size={16} />
                                                    )}
                                                    {taskAiOperations[task.id].rewrite?.expanded ? 
                                                        <ExpandLess fontSize="small" /> : 
                                                        <ExpandMore fontSize="small" />
                                                    }
                                                </Box>
                                                
                                                <Collapse in={taskAiOperations[task.id].rewrite?.expanded}>
                                                    <Paper 
                                                        elevation={1} 
                                                        sx={{ 
                                                            p: 2, 
                                                            mt: 1, 
                                                            bgcolor: 'grey.50',
                                                            border: '1px solid',
                                                            borderColor: 'grey.200'
                                                        }}
                                                    >
                                                        {taskAiOperations[task.id].rewrite?.loading && (
                                                            <Box display="flex" alignItems="center" gap={1}>
                                                                <CircularProgress size={16} />
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Generating rewrite...
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                        
                                                        {taskAiOperations[task.id].rewrite?.error && (
                                                            <Alert severity="error" sx={{ mb: 1 }}>
                                                                {taskAiOperations[task.id].rewrite.error}
                                                            </Alert>
                                                        )}
                                                        
                                                        {taskAiOperations[task.id].rewrite?.result && (
                                                            <Box>
                                                                {taskAiOperations[task.id].rewrite?.result?.title && (
                                                                    <Box mb={2}>
                                                                        <Typography variant="subtitle2" color="primary" gutterBottom>
                                                                            Enhanced Title:
                                                                        </Typography>
                                                                        <Typography 
                                                                            variant="body2" 
                                                                            sx={{ 
                                                                                p: 1, 
                                                                                bgcolor: 'white', 
                                                                                borderRadius: 1,
                                                                                fontWeight: 'medium'
                                                                            }}
                                                                        >
                                                                            {taskAiOperations[task.id].rewrite?.result?.title}
                                                                        </Typography>
                                                                    </Box>
                                                                )}
                                                                
                                                                {taskAiOperations[task.id].rewrite?.result?.user_story && (
                                                                    <Box>
                                                                        <Typography variant="subtitle2" color="primary" gutterBottom>
                                                                            User Story & Acceptance Criteria:
                                                                        </Typography>
                                                                        <Typography 
                                                                            component="pre" 
                                                                            variant="body2" 
                                                                            sx={{ 
                                                                                p: 1, 
                                                                                bgcolor: 'white', 
                                                                                borderRadius: 1,
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontFamily: 'monospace',
                                                                                lineHeight: 1.6,
                                                                                fontSize: '0.75rem'
                                                                            }}
                                                                        >
                                                                            {taskAiOperations[task.id].rewrite?.result?.user_story}
                                                                        </Typography>
                                                                    </Box>
                                                                )}
                                                                
                                                                <Box mt={2}>
                                                                    <Button 
                                                                        size="small" 
                                                                        variant="contained"
                                                                        onClick={async () => {
                                                                            if (!taskAiOperations[task.id].rewrite?.result) return;
                                                                            
                                                                            try {
                                                                                const updatedTask = await TaskService.updateTask(task.id, {
                                                                                    title: taskAiOperations[task.id].rewrite?.result?.title || '',
                                                                                    description: taskAiOperations[task.id].rewrite?.result?.user_story || ''
                                                                                });
                                                                                
                                                                                setTasks(tasks.map(t => 
                                                                                    t.id === updatedTask.id ? updatedTask : t
                                                                                ));
                                                                                
                                                                                // Clear the rewrite result after applying
                                                                                setTaskAiOperations(prev => ({
                                                                                    ...prev,
                                                                                    [task.id]: {
                                                                                        ...prev[task.id],
                                                                                        rewrite: {
                                                                                            ...prev[task.id].rewrite,
                                                                                            result: null,
                                                                                            expanded: false
                                                                                        }
                                                                                    }
                                                                                }));
                                                                            } catch (err) {
                                                                                console.error('Failed to apply rewrite:', err);
                                                                            }
                                                                        }}
                                                                    >
                                                                        Apply Rewrite
                                                                    </Button>
                                                                </Box>
                                                            </Box>
                                                        )}
                                                    </Paper>
                                                </Collapse>
                                            </Box>
                                        )}
                                    </Box>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {tasks.length === 0 && !loading && (
                <Box textAlign="center" py={4}>
                    <Typography variant="h6" color="text.secondary">
                        No tasks found
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mb={2}>
                        Create your first task to get started
                    </Typography>
                    <Button variant="contained" startIcon={<Add />} onClick={handleCreateTask}>
                        Create Task
                    </Button>
                </Box>
            )}

            {/* Task Form Dialog */}
            <Dialog open={showTaskForm} onClose={() => setShowTaskForm(false)} maxWidth="md" fullWidth>
                <DialogTitle>
                    {selectedTask ? 'Edit Task' : 'Create Task'}
                </DialogTitle>
                <DialogContent>
                    <TaskForm
                        task={selectedTask}
                        onSave={handleTaskSaved}
                        onCancel={() => setShowTaskForm(false)}
                    />
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
                <DialogTitle>Delete Task</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to delete "{taskToDelete?.title}"?
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
                    <Button onClick={confirmDeleteTask} color="error" variant="contained">
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Smart Summary Dialog */}
            <Dialog
                open={showSummaryDialog}
                onClose={() => setShowSummaryDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    <Box display="flex" alignItems="center" gap={1}>
                        <AutoAwesome color="primary" />
                        Smart Summary - {summaryTask?.title}
                    </Box>
                </DialogTitle>
                <DialogContent>
                    {summaryLoading && (
                        <Box display="flex" alignItems="center" gap={2} py={3}>
                            <CircularProgress size={24} />
                            <Typography>Generating smart summary...</Typography>
                        </Box>
                    )}

                    {summaryError && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {summaryError}
                        </Alert>
                    )}

                    {summary && !summaryLoading && (
                        <Box>
                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                                {summary}
                            </Typography>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowSummaryDialog(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            {/* Smart Rewrite Dialog */}
            <Dialog 
                open={showRewriteDialog} 
                onClose={() => setShowRewriteDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    <Box display="flex" alignItems="center" gap={1}>
                        <EditNote color="primary" />
                        Smart Rewrite - {rewriteTask?.title}
                    </Box>
                </DialogTitle>
                <DialogContent>
                    {rewriteLoading && (
                        <Box display="flex" alignItems="center" gap={2} py={3}>
                            <CircularProgress size={24} />
                            <Typography>Generating enhanced task description...</Typography>
                        </Box>
                    )}
                    
                    {rewriteError && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {rewriteError}
                        </Alert>
                    )}
                    
                    {rewrite && !rewriteLoading && (
                        <Box>
                            {rewrite.title && (
                                <Box mb={3}>
                                    <Typography variant="h6" gutterBottom color="primary">
                                        Enhanced Title:
                                    </Typography>
                                    <Typography variant="body1" sx={{ 
                                        p: 2, 
                                        bgcolor: 'grey.50', 
                                        borderRadius: 1,
                                        fontWeight: 'medium'
                                    }}>
                                        {rewrite.title}
                                    </Typography>
                                </Box>
                            )}
                            
                            {rewrite.user_story && (
                                <Box>
                                    <Typography variant="h6" gutterBottom color="primary">
                                        User Story & Acceptance Criteria:
                                    </Typography>
                                    <Typography 
                                        component="pre" 
                                        variant="body2" 
                                        sx={{ 
                                            p: 2, 
                                            bgcolor: 'grey.50', 
                                            borderRadius: 1,
                                            whiteSpace: 'pre-wrap',
                                            fontFamily: 'monospace',
                                            lineHeight: 1.6,
                                            fontSize: '0.875rem'
                                        }}
                                    >
                                        {rewrite.user_story}
                                    </Typography>
                                </Box>
                            )}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowRewriteDialog(false)}>Close</Button>
                    {rewrite && !rewriteLoading && (
                        <Button 
                            variant="contained" 
                            onClick={async () => {
                                if (!rewriteTask || !rewrite) return;
                                
                                try {
                                    // Update the task with the rewritten content
                                    const updatedTask = await TaskService.updateTask(rewriteTask.id, {
                                        title: rewrite.title,
                                        description: rewrite.user_story
                                    });
                                    
                                    // Update the task in the local state
                                    setTasks(tasks.map(task => 
                                        task.id === updatedTask.id ? updatedTask : task
                                    ));
                                    
                                    // Close the dialog
                                    setShowRewriteDialog(false);
                                    
                                    // Show success feedback (optional)
                                    // You could add a success snackbar here
                                } catch (err) {
                                    setRewriteError('Failed to apply rewrite');
                                    console.error('Failed to apply rewrite:', err);
                                }
                            }}
                        >
                            Apply Rewrite
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default TaskList;