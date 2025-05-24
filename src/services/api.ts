import axios from 'axios';
import { 
  FileInfo, 
  Quiz, 
  QuizGenerationRequest, 
  QuizGenerationResponse,
  QuizUpdateRequest 
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for quiz generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    } else if (error.response?.data?.message) {
      throw new Error(error.response.data.message);
    } else if (error.message) {
      throw new Error(error.message);
    } else {
      throw new Error('An unexpected error occurred');
    }
  }
);

export const apiService = {
  // File operations
  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  async getFiles(): Promise<FileInfo[]> {
    const response = await apiClient.get('/files');
    return response.data;
  },

  async getFileInfo(fileId: string): Promise<FileInfo> {
    const response = await apiClient.get(`/files/${fileId}`);
    return response.data;
  },

  async getExtractedText(fileId: string): Promise<any> {
    const response = await apiClient.get(`/files/${fileId}/text`);
    return response.data;
  },

  async deleteFile(fileId: string): Promise<void> {
    await apiClient.delete(`/files/${fileId}`);
  },

  // Quiz operations
  async generateQuiz(request: QuizGenerationRequest): Promise<Quiz> {
    const response = await apiClient.post<QuizGenerationResponse>('/generate-quiz', request);
    
    if (response.data.status === 'completed' && response.data.quiz) {
      return response.data.quiz;
    } else {
      throw new Error(response.data.message || 'Quiz generation failed');
    }
  },

  async getQuizzes(fileId?: string): Promise<Quiz[]> {
    const params = fileId ? { file_id: fileId } : {};
    const response = await apiClient.get('/quizzes', { params });
    return response.data;
  },

  async getQuiz(quizId: string): Promise<Quiz> {
    const response = await apiClient.get(`/quizzes/${quizId}`);
    return response.data;
  },

  async updateQuiz(quizId: string, updates: QuizUpdateRequest): Promise<Quiz> {
    const response = await apiClient.put(`/quizzes/${quizId}`, updates);
    return response.data;
  },

  async deleteQuiz(quizId: string): Promise<void> {
    await apiClient.delete(`/quizzes/${quizId}`);
  },

  async duplicateQuiz(quizId: string): Promise<Quiz> {
    const response = await apiClient.post(`/quizzes/${quizId}/duplicate`);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health', {
      baseURL: 'http://localhost:8000', // Direct to main app, not /api
    });
    return response.data;
  },
};

export default apiService;
