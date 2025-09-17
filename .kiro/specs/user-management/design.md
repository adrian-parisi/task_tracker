# Design Document

## Overview

This design implements proper user management for task assignees and reporters by replacing free text fields with searchable user dropdowns. The solution involves creating a new user API endpoint, updating the frontend components to use proper user selection interfaces, and enhancing the task display to show user information clearly.

## Architecture

### Backend Components

1. **Accounts App**
   - New Django app dedicated to user management
   - Contains CustomUser model extending AbstractUser
   - Provides foundation for future authentication and user management features

2. **CustomUser Model** (in accounts app)
   - Custom user model extending AbstractUser
   - Provides better control over user fields and validation
   - Foundation for future user management features

3. **User API Endpoint** (`/api/users/`)
   - Provides user search and listing functionality
   - Supports filtering by username, first name, and last name
   - Returns user data in a format suitable for frontend dropdowns

4. **Enhanced Task Serializer**
   - Already includes `assignee_detail` and `reporter_detail` fields
   - Updated to work with CustomUser model
   - Provides full user information for display purposes

### Frontend Components

1. **UserService**
   - New service for user-related API calls
   - Handles user search and retrieval

2. **UserAutocomplete Component**
   - Reusable component for user selection
   - Provides search functionality with debouncing
   - Displays user names in a user-friendly format

3. **Enhanced TaskForm**
   - Replaces text input with UserAutocomplete components
   - Handles user selection for both assignee and reporter

4. **Enhanced TaskList**
   - Updates task cards to display user information properly
   - Updates filters to use user selection instead of text input

## Components and Interfaces

### Backend API Design

#### User List/Search Endpoint
```
GET /api/users/?search=<query>
```

**Response Format:**
```json
{
  "results": [
    {
      "id": 1,
      "username": "john.doe",
      "first_name": "John",
      "last_name": "Doe",
      "display_name": "John Doe"
    }
  ]
}
```

#### User ViewSet
- Inherits from `ReadOnlyModelViewSet` (users should not be created/modified through task API)
- Implements search filtering on username, first_name, and last_name
- Returns only active users
- Includes computed `display_name` field

### Frontend Component Design

#### UserService Interface
```typescript
interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  display_name: string;
}

class UserService {
  static async searchUsers(query?: string): Promise<User[]>
}
```

#### UserAutocomplete Component
```typescript
interface UserAutocompleteProps {
  value: User | null;
  onChange: (user: User | null) => void;
  label: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
}
```

**Features:**
- Debounced search (300ms delay)
- Loading states during search
- Clear selection functionality
- Keyboard navigation support
- Display format: "First Last (username)" or just "username" if no first/last name

#### Enhanced Task Types
```typescript
interface Task {
  // ... existing fields
  assignee?: number; // for write operations
  reporter?: number; // for write operations
  assignee_detail?: User; // for display
  reporter_detail?: User; // for display
}
```

## Data Models

### CustomUser Model (accounts app)
- Create a custom user model extending AbstractUser in accounts/models.py
- Add additional fields for better user management (email required, display preferences)
- Fields: id, username, email, first_name, last_name, is_active, date_joined, last_login
- Provides foundation for future user management features

### Task Model Migration
- Update existing Task model to reference accounts.CustomUser instead of Django's User
- Create database migration to handle the model change
- Ensure existing user relationships are preserved

## Error Handling

### Backend Error Scenarios
1. **Invalid user ID in task creation/update**
   - Return 400 Bad Request with clear error message
   - Validate that user exists and is active

2. **User search API errors**
   - Handle database connection issues
   - Return appropriate HTTP status codes

### Frontend Error Scenarios
1. **User search failures**
   - Display error message in autocomplete
   - Allow manual retry
   - Graceful degradation to show current selection

2. **User selection validation**
   - Validate selected users exist before form submission
   - Clear invalid selections with user notification

## Testing Strategy

### Backend Tests
1. **User API Tests**
   - Test user listing without search
   - Test user search with various queries
   - Test filtering by username, first_name, last_name
   - Test case-insensitive search
   - Test pagination if implemented
   - Test that only active users are returned

2. **Task Integration Tests**
   - Test task creation with valid user assignments
   - Test task creation with invalid user IDs
   - Test task updates with user changes
   - Test serializer includes user details

### Frontend Tests
1. **UserService Tests**
   - Test user search API calls
   - Test error handling
   - Test response parsing

2. **UserAutocomplete Component Tests**
   - Test user search functionality
   - Test user selection
   - Test clearing selection
   - Test loading states
   - Test error states
   - Test keyboard navigation

3. **TaskForm Integration Tests**
   - Test assignee selection
   - Test reporter selection
   - Test form submission with users
   - Test editing existing tasks with users

4. **TaskList Integration Tests**
   - Test user display in task cards
   - Test user filtering
   - Test handling of tasks without assignees/reporters

### User Experience Testing
1. **Search Performance**
   - Verify debouncing works correctly
   - Test with large user datasets
   - Ensure responsive search results

2. **Accessibility**
   - Test keyboard navigation
   - Test screen reader compatibility
   - Test focus management

## Implementation Considerations

### Performance Optimizations
1. **Search Debouncing**
   - Implement 300ms debounce to reduce API calls
   - Cancel previous requests when new search is initiated

2. **User Caching**
   - Cache user search results for short periods
   - Implement simple in-memory cache for recently searched users

3. **Database Indexing**
   - Ensure User model has indexes on username, first_name, last_name
   - Consider full-text search for better performance with large user bases

### Security Considerations
1. **User Data Exposure**
   - Only expose necessary user fields (no email, sensitive data)
   - Ensure only active users are returned

2. **Authorization**
   - Verify user has permission to view user list
   - Consider rate limiting for search endpoint

### Backward Compatibility
1. **API Compatibility**
   - Maintain existing task API structure
   - Ensure existing clients continue to work

2. **Data Migration**
   - Create migration to introduce CustomUser model
   - Migrate existing User data to CustomUser
   - Update Task model foreign keys to reference CustomUser
   - Ensure all existing user relationships are preserved

## UI/UX Design

### User Selection Interface
- Use Material-UI Autocomplete component for consistency
- Display users as "First Last (username)" when both names available
- Fall back to username only when names not available
- Show loading spinner during search
- Show "No users found" message for empty results

### Task Card Display
- Show assignee with person icon
- Show reporter with different icon (e.g., flag or report icon)
- Use consistent typography and spacing
- Handle long names with ellipsis
- Show placeholder text for unassigned tasks

### Filter Interface
- Replace text input with user autocomplete
- Show selected user name in filter chip
- Allow clearing filter easily
- Maintain filter state across page refreshes