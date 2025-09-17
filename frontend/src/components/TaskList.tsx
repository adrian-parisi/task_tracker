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
    TextField,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Alert,
    CircularProgress
} from '@mui/material';
import {
    Add,
    Edit,
    Delete,
    FilterList,
    Assignment,
    AutoAwesome
} from '@mui/icons-material';
import { Task, TaskStatus, SmartSummaryResponse } from '../types/task';
import { TaskService } from '../services/taskService';
import TaskForm from './TaskForm';

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
    const [filters, setFilters] = useState({
        status: '',
        assignee: '',
        tag: ''
    });

    useEffect(() => {
        loadTasks();
    }, [filters]);

    const loadTasks = async () => {
        try {
            setLoading(true);
            setError('');
            const apiFilters = {
                ...filters,
                assignee: filters.assignee ? parseInt(filters.assignee) : undefined
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
        setSummaryTask(task);
        setSummaryLoading(true);
        setSummaryError('');
        setSummary('');
        setShowSummaryDialog(true);

        try {
            const response = await TaskService.getSmartSummary(task.id);
            setSummary(response.summary);
        } catch (err) {
            setSummaryError('Failed to generate summary');
            console.error('Failed to generate summary:', err);
        } finally {
            setSummaryLoading(false);
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
                        <Grid item xs={12} sm={4}>
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
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                size="small"
                                label="Assignee"
                                value={filters.assignee}
                                onChange={(e) => setFilters({ ...filters, assignee: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                size="small"
                                label="Tag"
                                value={filters.tag}
                                onChange={(e) => setFilters({ ...filters, tag: e.target.value })}
                            />
                        </Grid>
                    </Grid>
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
                                {((task.tags_detail || task.tags) && (task.tags_detail || task.tags).length > 0) && (
                                    <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                                        {(task.tags_detail || task.tags).map((tag) => (
                                            <Chip
                                                key={tag.id}
                                                label={tag.name}
                                                variant="outlined"
                                                size="small"
                                                color="secondary"
                                            />
                                        ))}
                                    </Box>
                                )}

                                {(task.assignee_detail || task.assignee) && (
                                    <Box display="flex" alignItems="center" gap={1}>
                                        <Assignment fontSize="small" color="action" />
                                        <Typography variant="body2" color="text.secondary">
                                            {(task.assignee_detail || task.assignee)?.username}
                                        </Typography>
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
        </Box>
    );
};

export default TaskList;