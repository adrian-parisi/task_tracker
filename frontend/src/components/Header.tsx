import React from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
    const { user, logout } = useAuth();

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    AI Task Management System
                </Typography>

                {user && (
                    <Box display="flex" alignItems="center" gap={2}>
                        <Typography variant="body2">
                            Welcome, {user.username}
                        </Typography>
                        <Button
                            color="inherit"
                            onClick={logout}
                            variant="outlined"
                            size="small"
                        >
                            Logout
                        </Button>
                    </Box>
                )}
            </Toolbar>
        </AppBar>
    );
};

export default Header;