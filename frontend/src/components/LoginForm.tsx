import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    TextField,
    Button,
    Typography,
    Alert,
    Container
} from '@mui/material';
import { AuthService, User } from '../services/authService';

interface LoginFormProps {
    onLogin: (user: User) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!username.trim() || !password.trim()) {
            setError('Username and password are required');
            return;
        }

        try {
            setLoading(true);
            setError('');
            
            const result = await AuthService.login(username.trim(), password);
            
            if (result.success && result.user) {
                onLogin(result.user);
            } else {
                setError(result.error || 'Login failed');
            }
        } catch (err) {
            setError('Login failed');
            console.error('Login error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                minHeight="100vh"
            >
                <Card sx={{ width: '100%', maxWidth: 400 }}>
                    <CardContent sx={{ p: 4 }}>
                        <Typography variant="h4" component="h1" gutterBottom align="center">
                            Login
                        </Typography>
                        
                        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
                            Sign in to access the task management system
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                                {error}
                            </Alert>
                        )}

                        <Box component="form" onSubmit={handleSubmit}>
                            <TextField
                                fullWidth
                                label="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                margin="normal"
                                required
                                autoFocus
                                disabled={loading}
                            />
                            
                            <TextField
                                fullWidth
                                label="Password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                margin="normal"
                                required
                                disabled={loading}
                            />
                            
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2 }}
                                disabled={loading || !username.trim() || !password.trim()}
                            >
                                {loading ? 'Signing in...' : 'Sign In'}
                            </Button>
                        </Box>

                        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                            <Typography variant="body2" color="text.secondary" align="center">
                                <strong>Demo Credentials:</strong><br />
                                Username: admin<br />
                                Password: admin123
                            </Typography>
                        </Box>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default LoginForm;