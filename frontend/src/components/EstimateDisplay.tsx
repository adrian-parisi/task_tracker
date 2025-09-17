import React from 'react';
import { 
    Card, 
    CardContent, 
    Typography, 
    CircularProgress, 
    Alert,
    Box,
    LinearProgress,
    Chip,
    List,
    ListItem,
    ListItemText,
    Link
} from '@mui/material';
import { Psychology, TrendingUp } from '@mui/icons-material';
import { SmartEstimateResponse } from '../types/task';

interface EstimateDisplayProps {
    estimate?: SmartEstimateResponse;
    loading: boolean;
    error?: string;
}

const EstimateDisplay: React.FC<EstimateDisplayProps> = ({ estimate, loading, error }) => {
    if (loading) {
        return (
            <Card sx={{ mt: 2 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <Psychology color="primary" />
                        <Typography variant="h6">Suggested Estimate</Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={2}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Calculating estimate...
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card sx={{ mt: 2 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <Psychology color="primary" />
                        <Typography variant="h6">Suggested Estimate</Typography>
                    </Box>
                    <Alert severity="error">
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (!estimate) {
        return null;
    }

    const confidenceColor = estimate.confidence >= 0.7 ? 'success' : 
                           estimate.confidence >= 0.5 ? 'warning' : 'error';

    return (
        <Card sx={{ mt: 2 }}>
            <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Psychology color="primary" />
                    <Typography variant="h6">Suggested Estimate</Typography>
                </Box>
                
                <Box mb={2}>
                    <Chip 
                        icon={<TrendingUp />}
                        label={`${estimate.suggested_points} Points`}
                        color="primary"
                        variant="outlined"
                        size="medium"
                    />
                </Box>

                <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Confidence: {(estimate.confidence * 100).toFixed(0)}%
                    </Typography>
                    <LinearProgress 
                        variant="determinate" 
                        value={estimate.confidence * 100}
                        color={confidenceColor}
                        sx={{ height: 8, borderRadius: 4 }}
                    />
                </Box>

                {estimate.rationale && (
                    <Box mb={2}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Rationale:</strong>
                        </Typography>
                        <Typography variant="body2">
                            {estimate.rationale}
                        </Typography>
                    </Box>
                )}

                {estimate.similar_task_ids && estimate.similar_task_ids.length > 0 && (
                    <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Similar Tasks ({estimate.similar_task_ids.length}):</strong>
                        </Typography>
                        <List dense>
                            {estimate.similar_task_ids.map((id, index) => (
                                <ListItem key={id} sx={{ py: 0.5, px: 0 }}>
                                    <ListItemText>
                                        <Link 
                                            href={`/tasks/${id}`} 
                                            underline="hover"
                                            sx={{ 
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 1,
                                                '&:hover': {
                                                    color: 'primary.main'
                                                }
                                            }}
                                        >
                                            <Chip 
                                                label={`#${index + 1}`} 
                                                size="small" 
                                                variant="outlined"
                                                sx={{ minWidth: 40 }}
                                            />
                                            Task {id.substring(0, 8)}...
                                        </Link>
                                    </ListItemText>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default EstimateDisplay;