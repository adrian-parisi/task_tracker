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
    Autocomplete
} from '@mui/material';
import { Task, TaskStatus, Tag, User } from '../types/task';
import { TaskService } from '../services/taskService';

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
        assignee: undefined as User | undefined,
        tags: [] as Tag[]
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        if (task) {
            setFormData({
                title: task.title,
                description: task.description,
                status: task.status,
                estimate: task.estimate?.toString() || '',
                assignee: task.assignee || undefined,
                tags: task.tags || []
            });
        }
    }, [task]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.title.trim()) {
            setError('Title is required');
            return;
        }

        try {
            setLoading(true);
            setError('');
            
            const taskData: Partial<Task> = {
                title: formData.title.trim(),
                description: formData.description.trim(),
                status: formData.status,
                estimate: formData.estimate ? parseInt(formData.estimate) : undefined,
                assignee: formData.assignee,
                tags: formData.tags
            };

            let savedTask: Task;
            if (task) {
                savedTask = await TaskService.updateTask(task.id, taskData);
            } else {
                savedTask = await TaskService.createTask(taskData);
            }
            
            onSave(savedTask);
        } catch (err) {
            setError(task ? 'Failed to update task' : 'Failed to create task');
            console.error('Failed to save task:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
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
                    <TextField
                        fullWidth
                        label="Estimate (points)"
                        type="number"
                        value={formData.estimate}
                        onChange={(e) => handleInputChange('estimate', e.target.value)}
                        inputProps={{ min: 0 }}
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Assignee (username)"
                        value={formData.assignee?.username || ''}
                        onChange={(e) => {
                            const username = e.target.value;
                            if (username) {
                                // For now, create a simple user object
                                // In a real app, this would be an autocomplete with user search
                                handleInputChange('assignee', {
                                    id: 0,
                                    username: username,
                                    email: `${username}@example.com`
                                });
                            } else {
                                handleInputChange('assignee', undefined);
                            }
                        }}
                        helperText="Enter username to assign task"
                    />
                </Grid>

                <Grid item xs={12}>
                    <Autocomplete
                        multiple
                        freeSolo
                        options={[]}
                        value={formData.tags.map(tag => tag.name)}
                        onChange={(_, newValue) => {
                            const tags = newValue.map((name, index) => ({
                                id: index,
                                name: typeof name === 'string' ? name : name
                            }));
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