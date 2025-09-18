import React, { useState, useEffect } from 'react';
import {
    Box,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    Alert,
    Grid,
    Chip,
    Autocomplete,
    CircularProgress,
    Typography,
    Paper
} from '@mui/material';
import { Psychology } from '@mui/icons-material';
import { Task, TaskStatus, SmartEstimateResponse, User } from '../types/task';
import { TaskService } from '../services/taskService';
import { sseService } from '../services/sseService';
import UserAutocomplete from './UserAutocomplete';

interface TaskFormProps {
    task?: Task | null;
    onSave: (task: Task) => void;
    onCancel: () => void;
}

const TaskForm: React.FC<TaskFormProps> = ({ task, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        status: TaskStatus.TODO,
        estimate: '',
        assignee: null as User | null,
        reporter: null as User | null,
        tags: [] as string[]
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [estimateLoading, setEstimateLoading] = useState(false);
    const [estimateError, setEstimateError] = useState<string>('');
    const [smartEstimate, setSmartEstimate] = useState<SmartEstimateResponse | null>(null);

    useEffect(() => {
        if (task) {
            // Use the user details directly since TaskUser is now the same as User
            const assigneeUser = task.assignee_detail || null;
            const reporterUser = task.reporter_detail || null;

            setFormData({
                title: task.title,
                description: task.description,
                status: task.status,
                estimate: task.estimate?.toString() || '',
                assignee: assigneeUser,
                reporter: reporterUser,
                tags: task.tags || []
            });
        }
    }, [task]);

    // Cleanup SSE connections on unmount
    useEffect(() => {
        return () => {
            sseService.disconnect();
        };
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        console.log('TaskForm - Form submitted');

        if (!formData.title.trim()) {
            setError('Title is required');
            return;
        }

        try {
            setLoading(true);
            setError('');

            const taskData: any = {
                title: formData.title.trim(),
                description: formData.description.trim(),
                status: formData.status,
                estimate: formData.estimate ? parseInt(formData.estimate) : undefined,
                // Send user IDs for assignee and reporter (backend expects primary keys)
                assignee: formData.assignee?.id || null,
                reporter: formData.reporter?.id || null,
                tags: formData.tags
            };

            console.log('TaskForm - Sending task data:', taskData);
            console.log('TaskForm - Form data state:', formData);

            let savedTask: Task;
            if (task) {
                // For updates, don't include project field
                savedTask = await TaskService.updateTask(task.id, taskData);
            } else {
                // For new tasks, include the project field
                taskData.project = "c34a8e03-7f0e-47f7-9cf6-428c07fb7d1b";
                savedTask = await TaskService.createTask(taskData);
            }

            console.log('TaskForm - Task saved successfully:', savedTask);
            onSave(savedTask);
        } catch (err) {
            console.error('Failed to save task - Full error:', err);
            console.error('Form data state:', formData);
            
            let errorMessage = task ? 'Failed to update task' : 'Failed to create task';
            
            // Check if it's a validation error
            if (err instanceof Error && 'status' in err) {
                const taskError = err as any;
                if (taskError.status === 400 && taskError.details) {
                    console.error('Validation errors:', taskError.details);
                    errorMessage = 'Validation failed. Please check the form data.';
                }
            }
            
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
        
        // Clear smart estimate when title or description changes
        if (field === 'title' || field === 'description') {
            setSmartEstimate(null);
            setEstimateError('');
        }
    };

    const handleSmartEstimate = async () => {
        if (!task) {
            setEstimateError('Smart Estimate is only available for existing tasks');
            return;
        }

        try {
            setEstimateLoading(true);
            setEstimateError('');
            setSmartEstimate(null);
            
            const estimateResult = await TaskService.getSmartEstimate(task.id);
            console.log('Estimate completed:', estimateResult);
            setSmartEstimate(estimateResult);
            setEstimateLoading(false);
        } catch (err) {
            setEstimateError('Failed to get estimate');
            setEstimateLoading(false);
            console.error('Failed to get estimate:', err);
        }
    };

    const canUseSmartEstimate = () => {
        return task && formData.title.trim().length > 0 && formData.description.trim().length > 0;
    };

    return (
        <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Title"
                        value={formData.title}
                        onChange={(e) => handleInputChange('title', e.target.value)}
                        required
                        error={!formData.title.trim() && error !== ''}
                        helperText={!formData.title.trim() && error !== '' ? 'Title is required' : ''}
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Description"
                        value={formData.description}
                        onChange={(e) => handleInputChange('description', e.target.value)}
                        multiline
                        rows={4}
                    />
                </Grid>

                <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                        <InputLabel>Status</InputLabel>
                        <Select
                            value={formData.status}
                            label="Status"
                            onChange={(e) => handleInputChange('status', e.target.value)}
                        >
                            <MenuItem value={TaskStatus.TODO}>To Do</MenuItem>
                            <MenuItem value={TaskStatus.IN_PROGRESS}>In Progress</MenuItem>
                            <MenuItem value={TaskStatus.BLOCKED}>Blocked</MenuItem>
                            <MenuItem value={TaskStatus.DONE}>Done</MenuItem>
                        </Select>
                    </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                    <Box>
                        <Box display="flex" gap={1} alignItems="flex-end">
                            <TextField
                                fullWidth
                                label="Estimate (points)"
                                type="number"
                                value={formData.estimate}
                                onChange={(e) => handleInputChange('estimate', e.target.value)}
                                inputProps={{ min: 0 }}
                            />
                            <Button
                                variant="outlined"
                                startIcon={estimateLoading ? <CircularProgress size={16} /> : <Psychology />}
                                onClick={handleSmartEstimate}
                                disabled={!canUseSmartEstimate() || estimateLoading}
                                sx={{ minWidth: 140, height: 56 }}
                            >
                                {estimateLoading ? 'Calculating...' : 'Smart Estimate'}
                            </Button>
                        </Box>
                        
                        {estimateError && (
                            <Alert severity="error" sx={{ mt: 1 }}>
                                {estimateError}
                            </Alert>
                        )}
                        
                        {smartEstimate && (
                            <Paper elevation={1} sx={{ mt: 2, p: 2, bgcolor: 'primary.50' }}>
                                <Typography variant="body2" color="primary" gutterBottom>
                                    <strong>AI Suggestion: {smartEstimate.suggested_points} points</strong>
                                </Typography>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Confidence: {(smartEstimate.confidence * 100).toFixed(0)}%
                                </Typography>
                                {smartEstimate.rationale && (
                                    <Typography variant="body2" color="text.secondary">
                                        {smartEstimate.rationale}
                                    </Typography>
                                )}
                                {smartEstimate.similar_task_ids && smartEstimate.similar_task_ids.length > 0 && (
                                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                        Based on {smartEstimate.similar_task_ids.length} similar task(s)
                                    </Typography>
                                )}
                                <Box mt={2}>
                                    <Button 
                                        size="small" 
                                        variant="contained"
                                        onClick={() => {
                                            handleInputChange('estimate', smartEstimate.suggested_points.toString());
                                            setSmartEstimate(null);
                                        }}
                                    >
                                        Apply Estimate
                                    </Button>
                                </Box>
                            </Paper>
                        )}
                    </Box>
                </Grid>

                <Grid item xs={12} sm={6}>
                    <UserAutocomplete
                        value={formData.assignee}
                        onChange={(user) => handleInputChange('assignee', user)}
                        label="Assignee"
                        placeholder="Search and select assignee..."
                        helperText="Select a user to assign this task to"
                    />
                </Grid>

                <Grid item xs={12} sm={6}>
                    <UserAutocomplete
                        value={formData.reporter}
                        onChange={(user) => handleInputChange('reporter', user)}
                        label="Reporter"
                        placeholder="Search and select reporter..."
                        helperText="Select the user who reported this task"
                    />
                </Grid>

                <Grid item xs={12}>
                    <Autocomplete
                        multiple
                        freeSolo
                        options={[]}
                        value={formData.tags}
                        onChange={(_, newValue) => {
                            const tags = newValue.map(name => 
                                typeof name === 'string' ? name : name
                            );
                            handleInputChange('tags', tags);
                        }}
                        renderTags={(value, getTagProps) =>
                            value.map((option, index) => (
                                <Chip
                                    variant="outlined"
                                    label={option}
                                    {...getTagProps({ index })}
                                    key={index}
                                />
                            ))
                        }
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="Tags"
                                placeholder="Add tags..."
                                helperText="Press Enter to add tags"
                            />
                        )}
                    />
                </Grid>
            </Grid>

            <Box display="flex" justifyContent="flex-end" gap={2} mt={3}>
                <Button onClick={onCancel} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    type="submit"
                    variant="contained"
                    disabled={loading || !formData.title.trim()}
                >
                    {loading ? 'Saving...' : (task ? 'Update' : 'Create')}
                </Button>
            </Box>
        </Box>
    );
};

export default TaskForm;