import React from 'react';
import { 
    Card, 
    CardContent, 
    Typography, 
    CircularProgress, 
    Alert,
    Box,
    Paper
} from '@mui/material';
import { Edit } from '@mui/icons-material';
import { SmartRewriteResponse } from '../types/task';

interface RewriteDisplayProps {
    rewrite?: SmartRewriteResponse;
    loading: boolean;
    error?: string;
}

const RewriteDisplay: React.FC<RewriteDisplayProps> = ({ rewrite, loading, error }) => {
    if (loading) {
        return (
            <Card sx={{ mt: 2 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <Edit color="primary" />
                        <Typography variant="h6">Enhanced Description</Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={2}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Generating enhanced description...
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
                        <Edit color="primary" />
                        <Typography variant="h6">Enhanced Description</Typography>
                    </Box>
                    <Alert severity="error">
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (!rewrite) {
        return null;
    }

    return (
        <Card sx={{ mt: 2 }}>
            <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Edit color="primary" />
                    <Typography variant="h6">Enhanced Description</Typography>
                </Box>
                
                {rewrite.title && (
                    <Box mb={2}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Enhanced Title:</strong>
                        </Typography>
                        <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Typography variant="body1" fontWeight="medium">
                                {rewrite.title}
                            </Typography>
                        </Paper>
                    </Box>
                )}

                {rewrite.user_story && (
                    <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>User Story:</strong>
                        </Typography>
                        <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Typography 
                                variant="body2" 
                                component="pre" 
                                sx={{ 
                                    fontFamily: 'monospace',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}
                            >
                                {rewrite.user_story}
                            </Typography>
                        </Paper>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default RewriteDisplay;