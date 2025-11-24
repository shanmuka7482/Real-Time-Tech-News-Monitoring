import axios from 'axios';

// The backend URL. Docker-compose will route `backend` to the right container.
// When running locally: 'http://localhost:8000'
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
});

export const getTopics = () => apiClient.get('/topics');
export const getTemporalData = () => apiClient.get('/topics/temporal');
export const getDocumentsForTopic = (topicId) => apiClient.get(`/documents/${topicId}`);
export const triggerInitialTrain = () => apiClient.post('/train');
