// Runtime configuration for Docker deployment
// API calls go through nginx proxy at /api
window.APP_CONFIG = {
    API_URL: ''  // Empty string = use relative paths, nginx will proxy /api/* to backend
};
