import React from 'react';
import { 
    Card, 
    CardContent, 
    Typography, 
    CircularProgress, 
    Alert,
    Box 
} from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';

interface SummaryDisplayProps {
    summary?: string;
    loading: boolean;
    error?: string;
}

const SummaryDisplay: React.FC<SummaryDisplayProps> = ({ summary, loading, error }) => {
    if (loading) {
        return (
            <Card sx={{ mt: 2 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <AutoAwesome color="primary" />
                        <Typography variant="h6">Task Summary</Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={2}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Generating summary...
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
                        <AutoAwesome color="primary" />
                        <Typography variant="h6">Task Summary</Typography>
                    </Box>
                    <Alert severity="error">
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (!summary) {
        return null;
    }

    return (
        <Card sx={{ mt: 2 }}>
            <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <AutoAwesome color="primary" />
                    <Typography variant="h6">Task Summary</Typography>
                </Box>
                <Typography variant="body1">
                    {summary}
                </Typography>
            </CardContent>
        </Card>
    );
};

export default SummaryDisplay;