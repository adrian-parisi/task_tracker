import React, { useState, useEffect, useCallback } from 'react';
import {
    Autocomplete,
    TextField,
    CircularProgress,
    Alert,
    Box,
    Typography
} from '@mui/material';
import { Person, Clear } from '@mui/icons-material';
import { User } from '../types/task';
import { UserService, UserServiceError } from '../services/userService';

export interface UserAutocompleteProps {
    value: User | null;
    onChange: (user: User | null) => void;
    label: string;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    error?: boolean;
    helperText?: string;
}

const UserAutocomplete: React.FC<UserAutocompleteProps> = ({
    value,
    onChange,
    label,
    placeholder = "Search users...",
    required = false,
    disabled = false,
    error = false,
    helperText
}) => {
    const [options, setOptions] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchError, setSearchError] = useState<string>('');
    const [inputValue, setInputValue] = useState('');
    const [open, setOpen] = useState(false);

    // Debounced search function
    const debouncedSearch = useCallback(
        debounce(async (query: string) => {
            if (!open) return; // Don't search if dropdown is closed
            
            try {
                setLoading(true);
                setSearchError('');
                const users = await UserService.searchUsers(query);
                setOptions(users);
            } catch (err) {
                if (err instanceof UserServiceError) {
                    setSearchError(err.message);
                } else {
                    setSearchError('Failed to search users');
                }
                setOptions([]);
            } finally {
                setLoading(false);
            }
        }, 300),
        [open]
    );

    // Effect to trigger search when input changes
    useEffect(() => {
        if (open) {
            debouncedSearch(inputValue);
        }
    }, [inputValue, debouncedSearch, open]);

    // Load initial users when dropdown opens
    useEffect(() => {
        if (open && options.length === 0 && !loading) {
            debouncedSearch('');
        }
    }, [open, options.length, loading, debouncedSearch]);

    // Format user display name
    const formatUserDisplay = (user: User): string => {
        if (user.first_name && user.last_name) {
            return `${user.first_name} ${user.last_name} (${user.username})`;
        }
        return user.username;
    };

    // Get option label for Autocomplete
    const getOptionLabel = (option: User): string => {
        return formatUserDisplay(option);
    };

    // Check if two users are equal
    const isOptionEqualToValue = (option: User, value: User): boolean => {
        return option.id === value.id;
    };

    return (
        <Box>
            <Autocomplete
                value={value}
                onChange={(_, newValue) => onChange(newValue)}
                inputValue={inputValue}
                onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
                open={open}
                onOpen={() => setOpen(true)}
                onClose={() => setOpen(false)}
                options={options}
                getOptionLabel={getOptionLabel}
                isOptionEqualToValue={isOptionEqualToValue}
                loading={loading}
                disabled={disabled}
                clearIcon={<Clear />}
                noOptionsText={
                    searchError ? (
                        <Box sx={{ p: 1 }}>
                            <Alert severity="error" sx={{ border: 'none', boxShadow: 'none' }}>
                                {searchError}
                            </Alert>
                        </Box>
                    ) : inputValue ? (
                        "No users found"
                    ) : (
                        "Start typing to search users"
                    )
                }
                renderInput={(params) => (
                    <TextField
                        {...params}
                        label={label}
                        placeholder={placeholder}
                        required={required}
                        error={error}
                        helperText={helperText}
                        InputProps={{
                            ...params.InputProps,
                            startAdornment: (
                                <Box sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                                    <Person color="action" fontSize="small" />
                                </Box>
                            ),
                            endAdornment: (
                                <React.Fragment>
                                    {loading ? <CircularProgress color="inherit" size={20} /> : null}
                                    {params.InputProps.endAdornment}
                                </React.Fragment>
                            ),
                        }}
                    />
                )}
                renderOption={(props, option) => (
                    <Box component="li" {...props} key={option.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                            <Person sx={{ mr: 1, color: 'action.active' }} fontSize="small" />
                            <Box>
                                <Typography variant="body2">
                                    {option.first_name && option.last_name 
                                        ? `${option.first_name} ${option.last_name}`
                                        : option.username
                                    }
                                </Typography>
                                {option.first_name && option.last_name && (
                                    <Typography variant="caption" color="text.secondary">
                                        {option.username}
                                    </Typography>
                                )}
                            </Box>
                        </Box>
                    </Box>
                )}
                // Accessibility props
                aria-label={label}
                componentsProps={{
                    popper: {
                        'aria-label': `${label} options`
                    }
                }}
            />
        </Box>
    );
};

// Debounce utility function
function debounce<T extends (...args: any[]) => any>(
    func: T,
    delay: number
): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

export default UserAutocomplete;