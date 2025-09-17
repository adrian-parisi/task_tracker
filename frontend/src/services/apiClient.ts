import axios, { AxiosInstance } from 'axios';

const apiClient: AxiosInstance = axios.create({
    baseURL: 'http://localhost:8000/api/',
    headers: {
        'Content-Type': 'application/json'
    },
    withCredentials: true
});

// Add CSRF token interceptor
apiClient.interceptors.request.use((config) => {
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.error('Unauthorized access - redirecting to login');
            // Could redirect to login page here
        }
        return Promise.reject(error);
    }
);

export default apiClient;