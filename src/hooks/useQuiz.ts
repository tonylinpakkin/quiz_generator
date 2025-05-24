import { useState, useCallback } from 'react';
import { Quiz, QuizGenerationRequest, QuizUpdateRequest, UseQuizResult } from '../types';
import { apiService } from '../services/api';

export const useQuiz = (): UseQuizResult => {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQuizzes = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.getQuizzes();
      setQuizzes(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load quizzes');
    } finally {
      setLoading(false);
    }
  }, []);

  const generateQuiz = useCallback(async (request: QuizGenerationRequest): Promise<Quiz> => {
    setLoading(true);
    setError(null);
    
    try {
      const quiz = await apiService.generateQuiz(request);
      setQuizzes(prev => [quiz, ...prev]);
      return quiz;
    } catch (err: any) {
      setError(err.message || 'Failed to generate quiz');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateQuiz = useCallback(async (quizId: string, updates: QuizUpdateRequest): Promise<Quiz> => {
    setLoading(true);
    setError(null);
    
    try {
      const updatedQuiz = await apiService.updateQuiz(quizId, updates);
      setQuizzes(prev => prev.map(quiz => 
        quiz.id === quizId ? updatedQuiz : quiz
      ));
      return updatedQuiz;
    } catch (err: any) {
      setError(err.message || 'Failed to update quiz');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteQuiz = useCallback(async (quizId: string): Promise<void> => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.deleteQuiz(quizId);
      setQuizzes(prev => prev.filter(quiz => quiz.id !== quizId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete quiz');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const duplicateQuiz = useCallback(async (quizId: string): Promise<Quiz> => {
    setLoading(true);
    setError(null);
    
    try {
      const duplicatedQuiz = await apiService.duplicateQuiz(quizId);
      setQuizzes(prev => [duplicatedQuiz, ...prev]);
      return duplicatedQuiz;
    } catch (err: any) {
      setError(err.message || 'Failed to duplicate quiz');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    quizzes,
    loading,
    error,
    loadQuizzes,
    generateQuiz,
    updateQuiz,
    deleteQuiz,
    duplicateQuiz,
  };
};

export default useQuiz;
