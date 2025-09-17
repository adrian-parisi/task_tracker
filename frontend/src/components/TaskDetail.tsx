import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Chip,
    Grid,
    Divider,
    Alert,
    CircularProgress,
    Paper,
    IconButton
} from '@mui/material';
import {
    AutoAwesome,
    Psychology,
    Edit,
    Assignment,
    Schedule,
    Person,
    Tag as TagIcon,
    ArrowBack
} from '@mui/icons-material';
import { Task, SmartSummaryResponse, SmartEstimateResponse, SmartRewriteResponse, TaskStatus } from '../types/task';
import { TaskService } from '../services/taskService';
import SummaryDisplay from './SummaryDisplay';
import EstimateDisplay from './EstimateDisplay';
import RewriteDisplay from './RewriteDisplay';

interface TaskDetailProps {
    taskId: string;
    onBack?: () => void;
    onEdit?: (task: Task) => void;
}

const TaskDetail: React.FC<TaskDetailProps> = ({ taskId, onBack, onEdit }) => {
    const [task, setTask] = useState<Task | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');
    
    // AI tool states
    const [summary, setSummary] = useState<SmartSummaryResponse | null>(null);
    const [estimate, setEstimate] = useState<SmartEstimateResponse | undefined>(undefined);
    const [rewrite, setRewrite] = useState<SmartRewriteResponse | undefined>(undefined);
    const [aiLoading, setAiLoading] = useState({
        summary: false,
        estimate: false,
        rewrite: false
    });
    const [aiErrors, setAiErrors] = useState({
        summary: '',
        estimate: '',
        rewrite: ''
    });

    useEffect(() => {
        loadTask();
    }, [taskId]);

    const loadTask = async () => {
        try {
            setLoading(true);
            setError('');
            const taskData = await TaskService.getTask(taskId);
            setTask(taskData);
        } catch (err) {
            setError('Failed to load task');
            console.error('Failed to load task:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSmartSummary = async () => {
        try {
            setAiLoading(prev => ({ ...prev, summary: true }));
            setAiErrors(prev => ({ ...prev, summary: '' }));
            const summaryData = await TaskService.getSmartSummary(taskId);
            setSummary(summaryData);
        } catch (err) {
            setAiErrors(prev => ({ ...prev, summary: 'Failed to generate summary' }));
            console.error('Failed to get smart summary:', err);
        } finally {
            setAiLoading(prev => ({ ...prev, summary: false }));
        }
    };

    const handleSmartEstimate = async () => {
        try {
            setAiLoading(prev => ({ ...prev, estimate: true }));
            setAiErrors(prev => ({ ...prev, estimate: '' }));
            const estimateData = await TaskService.getSmartEstimate(taskId);
            setEstimate(estimateData);
        } catch (err) {
            setAiErrors(prev => ({ ...prev, estimate: 'Failed to calculate estimate' }));
            console.error('Failed to get smart estimate:', err);
        } finally {
            setAiLoading(prev => ({ ...prev, estimate: false }));
        }
    };

    const handleSmartRewrite = async () => {
        try {
            setAiLoading(prev => ({ ...prev, rewrite: true }));
            setAiErrors(prev => ({ ...prev, rewrite: '' }));
            const rewriteData = await TaskService.getSmartRewrite(taskId);
            setRewrite(rewriteData);
        } catch (err) {
            setAiErrors(prev => ({ ...prev, rewrite: 'Failed to generate rewrite' }));
            console.error('Failed to get smart rewrite:', err);
        } finally {
            setAiLoading(prev => ({ ...prev, rewrite: false }));
        }
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

    if (error || !task) {
        return (
            <Alert severity="error">
                {error || 'Task not found'}
            </Alert>
        );
    }

    return (
        <Box p={3}>
            {/* Header */}
            <Box display="flex" alignItems="center" gap={2} mb={3}>
                {onBack && (
                    <IconButton onClick={onBack}>
                        <ArrowBack />
                    </IconButton>
                )}
                <Typography variant="h4" component="h1" flexGrow={1}>
                    {task.title}
                </Typography>
                {onEdit && (
                    <Button
                        variant="outlined"
                        startIcon={<Edit />}
                        onClick={() => onEdit(task)}
                    >
                        Edit
                    </Button>
                )}
            </Box>

            <Grid container spacing={3}>
                {/* Task Information */}
                <Grid item xs={12} md={8}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Task Details
                            </Typography>
                            
                            <Box mb={3}>
                                <Typography variant="body1" paragraph>
                                    {task.description || 'No description provided'}
                                </Typography>
                            </Box>

                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                                        <Schedule color="action" />
                                        <Typography variant="body2" color="text.secondary">
                                            Status:
                                        </Typography>
                                        <Chip 
                                            label={task.status.replace('_', ' ')}
                                            color={getStatusColor(task.status)}
                                            size="small"
                                        />
                                    </Box>
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    {task.estimate && (
                                        <Box display="flex" alignItems="center" gap={1} mb={2}>
                                            <Psychology color="action" />
                                            <Typography variant="body2" color="text.secondary">
                                                Estimate: {task.estimate} points
                                            </Typography>
                                        </Box>
                                    )}
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    {task.assignee && (
                                        <Box display="flex" alignItems="center" gap={1} mb={2}>
                                            <Person color="action" />
                                            <Typography variant="body2" color="text.secondary">
                                                Assignee: {task.assignee.username}
                                            </Typography>
                                        </Box>
                                    )}
                                </Grid>

                                <Grid item xs={12} sm={6}>
                                    {task.reporter && (
                                        <Box display="flex" alignItems="center" gap={1} mb={2}>
                                            <Assignment color="action" />
                                            <Typography variant="body2" color="text.secondary">
                                                Reporter: {task.reporter.username}
                                            </Typography>
                                        </Box>
                                    )}
                                </Grid>

                                {task.tags && task.tags.length > 0 && (
                                    <Grid item xs={12}>
                                        <Box display="flex" alignItems="center" gap={1} mb={2}>
                                            <TagIcon color="action" />
                                            <Typography variant="body2" color="text.secondary">
                                                Tags:
                                            </Typography>
                                            <Box display="flex" gap={1} flexWrap="wrap">
                                                {task.tags.map((tag) => (
                                                    <Chip
                                                        key={tag.id}
                                                        label={tag.name}
                                                        variant="outlined"
                                                        size="small"
                                                    />
                                                ))}
                                            </Box>
                                        </Box>
                                    </Grid>
                                )}
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>

                {/* AI Tools */}
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                AI Tools
                            </Typography>
                            <Typography variant="body2" color="text.secondary" paragraph>
                                Use AI to enhance your task management
                            </Typography>

                            <Box display="flex" flexDirection="column" gap={2}>
                                <Button
                                    variant="outlined"
                                    startIcon={<AutoAwesome />}
                                    onClick={handleSmartSummary}
                                    disabled={aiLoading.summary}
                                    fullWidth
                                >
                                    {aiLoading.summary ? 'Generating...' : 'Smart Summary'}
                                </Button>

                                <Button
                                    variant="outlined"
                                    startIcon={<Psychology />}
                                    onClick={handleSmartEstimate}
                                    disabled={aiLoading.estimate}
                                    fullWidth
                                >
                                    {aiLoading.estimate ? 'Calculating...' : 'Smart Estimate'}
                                </Button>

                                <Button
                                    variant="outlined"
                                    startIcon={<Edit />}
                                    onClick={handleSmartRewrite}
                                    disabled={aiLoading.rewrite}
                                    fullWidth
                                >
                                    {aiLoading.rewrite ? 'Rewriting...' : 'Smart Rewrite'}
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* AI Results */}
                <Grid item xs={12}>
                    <SummaryDisplay 
                        summary={summary?.summary} 
                        loading={aiLoading.summary}
                        error={aiErrors.summary}
                    />
                    <EstimateDisplay 
                        estimate={estimate} 
                        loading={aiLoading.estimate}
                        error={aiErrors.estimate}
                    />
                    <RewriteDisplay 
                        rewrite={rewrite} 
                        loading={aiLoading.rewrite}
                        error={aiErrors.rewrite}
                    />
                </Grid>
            </Grid>
        </Box>
    );
};

export default TaskDetail;