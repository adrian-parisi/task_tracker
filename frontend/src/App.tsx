import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, CircularProgress } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginForm from './components/LoginForm';
import Header from './components/Header';
import TaskList from './components/TaskList';
import TaskDetail from './components/TaskDetail';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function AppContent() {
  const { user, loading, login } = useAuth();
  const [currentView, setCurrentView] = useState<'list' | 'detail'>('list');
  const [selectedTaskId, setSelectedTaskId] = useState<string>('');

  const handleViewTask = (taskId: string) => {
    setSelectedTaskId(taskId);
    setCurrentView('detail');
  };

  const handleBackToList = () => {
    setCurrentView('list');
    setSelectedTaskId('');
  };

  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return <LoginForm onLogin={login} />;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Header />
      
      <Container maxWidth="xl" sx={{ mt: 2 }}>
        {currentView === 'list' ? (
          <TaskList />
        ) : (
          <TaskDetail 
            taskId={selectedTaskId}
            onBack={handleBackToList}
          />
        )}
      </Container>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;