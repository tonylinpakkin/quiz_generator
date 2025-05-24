import React, { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import QuizDisplay from './components/QuizDisplay';
import QuizEditor from './components/QuizEditor';
import LoadingSpinner from './components/LoadingSpinner';
import { Quiz, FileInfo, QuizGenerationRequest } from './types';
import { apiService } from './services/api';
import { useQuiz } from './hooks/useQuiz';

type View = 'upload' | 'quiz-list' | 'quiz-view' | 'quiz-edit';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('upload');
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [selectedQuiz, setSelectedQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    quizzes,
    loadQuizzes,
    generateQuiz,
    updateQuiz,
    deleteQuiz,
    loading: quizLoading
  } = useQuiz();

  useEffect(() => {
    loadFiles();
    loadQuizzes();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await apiService.getFiles();
      setFiles(response);
    } catch (err) {
      setError('Failed to load files');
    }
  };

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.uploadFile(file);
      await loadFiles();
      setCurrentView('quiz-list');
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateQuiz = async (fileId: string, options: Partial<QuizGenerationRequest>) => {
    setLoading(true);
    setError(null);
    
    try {
      const quiz = await generateQuiz({
        file_id: fileId,
        num_questions: options.num_questions || 5,
        question_types: options.question_types || ['multiple_choice'],
        difficulty_level: options.difficulty_level || 'medium',
        focus_topics: options.focus_topics
      });
      
      setSelectedQuiz(quiz);
      setCurrentView('quiz-view');
      await loadQuizzes();
    } catch (err: any) {
      setError(err.message || 'Quiz generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuizSelect = (quiz: Quiz) => {
    setSelectedQuiz(quiz);
    setCurrentView('quiz-view');
  };

  const handleQuizEdit = (quiz: Quiz) => {
    setSelectedQuiz(quiz);
    setCurrentView('quiz-edit');
  };

  const handleQuizUpdate = async (quizId: string, updates: any) => {
    try {
      const updatedQuiz = await updateQuiz(quizId, updates);
      setSelectedQuiz(updatedQuiz);
      setCurrentView('quiz-view');
      await loadQuizzes();
    } catch (err: any) {
      setError(err.message || 'Quiz update failed');
    }
  };

  const handleQuizDelete = async (quizId: string) => {
    if (window.confirm('Are you sure you want to delete this quiz?')) {
      try {
        await deleteQuiz(quizId);
        if (selectedQuiz?.id === quizId) {
          setSelectedQuiz(null);
        }
        setCurrentView('quiz-list');
        await loadQuizzes();
      } catch (err: any) {
        setError(err.message || 'Quiz deletion failed');
      }
    }
  };

  const renderHeader = () => (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <i className="fas fa-brain text-3xl text-blue-600 mr-3"></i>
            <h1 className="text-3xl font-bold text-gray-900">Quiz Generator</h1>
          </div>
          <nav className="flex space-x-4">
            <button
              onClick={() => setCurrentView('upload')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                currentView === 'upload'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <i className="fas fa-upload mr-2"></i>Upload
            </button>
            <button
              onClick={() => setCurrentView('quiz-list')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                currentView === 'quiz-list'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <i className="fas fa-list mr-2"></i>Quizzes
            </button>
          </nav>
        </div>
      </div>
    </header>
  );

  const renderContent = () => {
    if (loading || quizLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner message="Processing..." />
        </div>
      );
    }

    switch (currentView) {
      case 'upload':
        return (
          <FileUpload
            onFileUpload={handleFileUpload}
            onGenerateQuiz={handleGenerateQuiz}
            files={files}
            error={error}
          />
        );
      
      case 'quiz-list':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Your Quizzes</h2>
              <button
                onClick={() => setCurrentView('upload')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                <i className="fas fa-plus mr-2"></i>Create New Quiz
              </button>
            </div>
            
            {quizzes.length === 0 ? (
              <div className="text-center py-12">
                <i className="fas fa-clipboard-list text-6xl text-gray-300 mb-4"></i>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No quizzes yet</h3>
                <p className="text-gray-500 mb-4">Upload a document to generate your first quiz</p>
                <button
                  onClick={() => setCurrentView('upload')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Get Started
                </button>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {quizzes.map((quiz) => (
                  <div key={quiz.id} className="bg-white p-6 rounded-lg shadow border">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{quiz.title}</h3>
                    <p className="text-gray-600 text-sm mb-4">{quiz.description}</p>
                    <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
                      <span>{quiz.questions.length} questions</span>
                      <span>{new Date(quiz.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleQuizSelect(quiz)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleQuizEdit(quiz)}
                        className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleQuizDelete(quiz.id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm"
                      >
                        <i className="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      
      case 'quiz-view':
        return selectedQuiz ? (
          <QuizDisplay
            quiz={selectedQuiz}
            onEdit={() => handleQuizEdit(selectedQuiz)}
            onDelete={() => handleQuizDelete(selectedQuiz.id)}
            onBack={() => setCurrentView('quiz-list')}
          />
        ) : null;
      
      case 'quiz-edit':
        return selectedQuiz ? (
          <QuizEditor
            quiz={selectedQuiz}
            onSave={(updates) => handleQuizUpdate(selectedQuiz.id, updates)}
            onCancel={() => setCurrentView('quiz-view')}
          />
        ) : null;
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {renderHeader()}
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              <div className="flex">
                <i className="fas fa-exclamation-circle mr-2 mt-0.5"></i>
                <span>{error}</span>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
            </div>
          )}
          
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;
