import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with base configuration
const apiClient = axios.create({
    baseURL: process.env.REACT_APP_API_URL || '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        // Add timestamp to prevent caching
        config.params = {
            ...config.params,
            _t: Date.now()
        };
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        // Handle common errors
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;

            if (status === 500) {
                toast.error('Server error. Please try again later.');
            } else if (status === 404) {
                toast.error('Resource not found.');
            } else if (status === 400) {
                toast.error(data.error || 'Bad request.');
            } else {
                toast.error(data.error || 'An error occurred.');
            }
        } else if (error.request) {
            // Network error
            toast.error('Network error. Please check your connection.');
        } else {
            // Other error
            toast.error('An unexpected error occurred.');
        }

        return Promise.reject(error);
    }
);

// API service methods
export const apiService = {
    // User authentication
    login: (username) => apiClient.post('/users/login', { username }),
    getUser: (userId) => apiClient.get(`/users/${userId}`),

    // Building data
    getBuildingsInArea: (bounds, refresh = false) => {
        const boundsStr = bounds.join(',');
        return apiClient.get(`/buildings/area?bounds=${boundsStr}&refresh=${refresh}`);
    },
    getBuildingDetails: (buildingId) => apiClient.get(`/buildings/${buildingId}`),
    filterBuildings: (filters, bounds) => apiClient.post('/buildings/filter', { filters, bounds }),
    refreshBuildingData: (bounds) => apiClient.post('/buildings/refresh', { bounds }),
    getBuildingStatistics: (bounds) => {
        const boundsStr = bounds ? bounds.join(',') : '';
        return apiClient.get(`/buildings/statistics${boundsStr ? `?bounds=${boundsStr}` : ''}`);
    },

    // Calgary Open Data specific endpoints
    get3DBuildings: (bounds, limit = 500) => {
        const params = new URLSearchParams();
        if (bounds) params.append('bounds', bounds.join(','));
        if (limit) params.append('limit', limit);
        return apiClient.get(`/buildings/3d?${params.toString()}`);
    },
    getZoningData: (bounds, limit = 1000) => {
        const params = new URLSearchParams();
        if (bounds) params.append('bounds', bounds.join(','));
        if (limit) params.append('limit', limit);
        return apiClient.get(`/buildings/zoning?${params.toString()}`);
    },
    getPropertyAssessments: (parcelIds = null, limit = 1000) => {
        const params = new URLSearchParams();
        if (parcelIds && parcelIds.length > 0) params.append('parcel_ids', parcelIds.join(','));
        if (limit) params.append('limit', limit);
        return apiClient.get(`/buildings/assessments?${params.toString()}`);
    },

    // LLM query processing
    processQuery: (query, userId, bounds) =>
        apiClient.post('/query/process', { query, user_id: userId, bounds }),
    parseQuery: (query) => apiClient.post('/query/parse', { query }),
    getQuerySuggestions: () => apiClient.get('/query/suggestions'),
    validateFilters: (filters) => apiClient.post('/query/validate', { filters }),

    // Project management
    saveProject: (userId, name, description, filters) =>
        apiClient.post('/projects/save', { user_id: userId, name, description, filters }),
    getUserProjects: (userId) => apiClient.get(`/projects/user/${userId}`),
    getProject: (projectId) => apiClient.get(`/projects/${projectId}`),
    updateProject: (projectId, data) => apiClient.put(`/projects/${projectId}`, data),
    deleteProject: (projectId) => apiClient.delete(`/projects/${projectId}`),
    loadProject: (projectId, applyFilters = true) =>
        apiClient.post(`/projects/${projectId}/load?apply_filters=${applyFilters}`),

    // Health check
    healthCheck: () => apiClient.get('/health'),
};

export { apiClient };
export default apiService; 