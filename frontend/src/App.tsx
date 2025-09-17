import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import { Assignment } from '@mui/icons-material';
import TaskList from './components/TaskList';
import TaskDetail from './components/TaskDetail';
import { Task } from './types/task';

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

function App() {
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

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Assignment sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              AI Task Tools
            </Typography>
          </Toolbar>
        </AppBar>
        
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
    </ThemeProvider>
  );
}

export default App;