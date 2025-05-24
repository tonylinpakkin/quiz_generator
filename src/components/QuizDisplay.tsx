import React, { useState } from 'react';
import { Quiz, QuizQuestion } from '../types';

interface QuizDisplayProps {
  quiz: Quiz;
  onEdit: () => void;
  onDelete: () => void;
  onBack: () => void;
}

const QuizDisplay: React.FC<QuizDisplayProps> = ({
  quiz,
  onEdit,
  onDelete,
  onBack
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [quizMode, setQuizMode] = useState<'study' | 'test'>('study');

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const totalQuestions = quiz.questions.length;
  const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;

  const handleAnswerSelect = (questionId: string, answer: string) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else if (quizMode === 'test') {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleFinishQuiz = () => {
    setShowResults(true);
  };

  const calculateScore = () => {
    let correct = 0;
    quiz.questions.forEach(question => {
      const userAnswer = userAnswers[question.id];
      if (userAnswer === question.correct_answer) {
        correct++;
      }
    });
    return { correct, total: totalQuestions, percentage: (correct / totalQuestions) * 100 };
  };

  const renderQuestionContent = (question: QuizQuestion, showAnswer: boolean = false) => {
    const userAnswer = userAnswers[question.id];
    const isCorrect = userAnswer === question.correct_answer;

    return (
      <div className="quiz-question">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex-1">
            {question.question}
          </h3>
          <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded ml-4">
            {question.difficulty}
          </span>
        </div>

        {question.question_type === 'multiple_choice' && question.options && (
          <div className="space-y-2">
            {question.options.map((option, index) => {
              const isSelected = userAnswer === option;
              const isCorrectOption = option === question.correct_answer;
              
              let optionClass = 'quiz-option';
              if (showAnswer) {
                if (isCorrectOption) {
                  optionClass += ' correct';
                } else if (isSelected && !isCorrectOption) {
                  optionClass += ' incorrect';
                }
              } else if (isSelected) {
                optionClass += ' selected';
              }

              return (
                <button
                  key={index}
                  className={optionClass}
                  onClick={() => !showAnswer && handleAnswerSelect(question.id, option)}
                  disabled={showAnswer}
                >
                  <span className="font-medium mr-3">
                    {String.fromCharCode(65 + index)}.
                  </span>
                  <span className="flex-1 text-left">{option}</span>
                  {showAnswer && isCorrectOption && (
                    <i className="fas fa-check text-green-600"></i>
                  )}
                  {showAnswer && isSelected && !isCorrectOption && (
                    <i className="fas fa-times text-red-600"></i>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {question.question_type === 'true_false' && question.options && (
          <div className="space-y-2">
            {question.options.map((option) => {
              const isSelected = userAnswer === option;
              const isCorrectOption = option === question.correct_answer;
              
              let optionClass = 'quiz-option';
              if (showAnswer) {
                if (isCorrectOption) {
                  optionClass += ' correct';
                } else if (isSelected && !isCorrectOption) {
                  optionClass += ' incorrect';
                }
              } else if (isSelected) {
                optionClass += ' selected';
              }

              return (
                <button
                  key={option}
                  className={optionClass}
                  onClick={() => !showAnswer && handleAnswerSelect(question.id, option)}
                  disabled={showAnswer}
                >
                  <span className="flex-1 text-left">{option}</span>
                  {showAnswer && isCorrectOption && (
                    <i className="fas fa-check text-green-600"></i>
                  )}
                  {showAnswer && isSelected && !isCorrectOption && (
                    <i className="fas fa-times text-red-600"></i>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {question.question_type === 'short_answer' && (
          <div className="space-y-3">
            <textarea
              className="textarea-field"
              rows={3}
              placeholder="Enter your answer..."
              value={userAnswer || ''}
              onChange={(e) => handleAnswerSelect(question.id, e.target.value)}
              disabled={showAnswer}
            />
            {showAnswer && (
              <div className="bg-green-50 border border-green-200 p-3 rounded">
                <p className="text-sm font-medium text-green-800 mb-1">Suggested Answer:</p>
                <p className="text-green-700">{question.correct_answer}</p>
              </div>
            )}
          </div>
        )}

        {(showAnswer || quizMode === 'study') && question.explanation && (
          <div className="mt-4 bg-blue-50 border border-blue-200 p-3 rounded">
            <p className="text-sm font-medium text-blue-800 mb-1">Explanation:</p>
            <p className="text-blue-700">{question.explanation}</p>
          </div>
        )}
      </div>
    );
  };

  if (showResults) {
    const score = calculateScore();
    
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            Back to Quizzes
          </button>
        </div>

        <div className="card text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Quiz Complete!</h2>
          
          <div className="mb-6">
            <div className="text-6xl font-bold text-blue-600 mb-2">
              {Math.round(score.percentage)}%
            </div>
            <p className="text-lg text-gray-600">
              You got {score.correct} out of {score.total} questions correct
            </p>
          </div>

          <div className="flex justify-center space-x-4">
            <button
              onClick={() => {
                setShowResults(false);
                setCurrentQuestionIndex(0);
                setUserAnswers({});
              }}
              className="btn-primary"
            >
              <i className="fas fa-redo mr-2"></i>
              Retake Quiz
            </button>
            <button
              onClick={() => setShowResults(false)}
              className="btn-secondary"
            >
              <i className="fas fa-eye mr-2"></i>
              Review Answers
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-900">Review</h3>
          {quiz.questions.map((question, index) => (
            <div key={question.id}>
              <div className="flex items-center mb-2">
                <span className="text-sm font-medium text-gray-600 mr-2">
                  Question {index + 1}:
                </span>
                {userAnswers[question.id] === question.correct_answer ? (
                  <span className="text-green-600 text-sm">
                    <i className="fas fa-check mr-1"></i>Correct
                  </span>
                ) : (
                  <span className="text-red-600 text-sm">
                    <i className="fas fa-times mr-1"></i>Incorrect
                  </span>
                )}
              </div>
              {renderQuestionContent(question, true)}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="text-gray-600 hover:text-gray-800"
        >
          <i className="fas fa-arrow-left mr-2"></i>
          Back to Quizzes
        </button>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setQuizMode(quizMode === 'study' ? 'test' : 'study')}
            className={`px-3 py-1 rounded text-sm ${
              quizMode === 'study' 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            <i className={`fas ${quizMode === 'study' ? 'fa-book' : 'fa-clipboard-check'} mr-1`}></i>
            {quizMode === 'study' ? 'Study Mode' : 'Test Mode'}
          </button>
          <button onClick={onEdit} className="btn-secondary text-sm">
            <i className="fas fa-edit mr-1"></i>Edit
          </button>
          <button onClick={onDelete} className="btn-danger text-sm">
            <i className="fas fa-trash mr-1"></i>Delete
          </button>
        </div>
      </div>

      {/* Quiz Info */}
      <div className="card">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{quiz.title}</h1>
            {quiz.description && (
              <p className="text-gray-600 mt-1">{quiz.description}</p>
            )}
          </div>
          <div className="text-right text-sm text-gray-500">
            <p>{totalQuestions} questions</p>
            <p>Created {new Date(quiz.created_at).toLocaleDateString()}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Question {currentQuestionIndex + 1} of {totalQuestions}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Current Question */}
      {renderQuestionContent(currentQuestion, quizMode === 'study')}

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <button
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <i className="fas fa-chevron-left mr-2"></i>
          Previous
        </button>

        <div className="flex space-x-3">
          {quizMode === 'test' && (
            <button
              onClick={handleFinishQuiz}
              className="btn-primary"
            >
              <i className="fas fa-flag-checkered mr-2"></i>
              Finish Quiz
            </button>
          )}
          
          <button
            onClick={handleNext}
            disabled={currentQuestionIndex === totalQuestions - 1 && quizMode === 'study'}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentQuestionIndex === totalQuestions - 1 ? 'Finish' : 'Next'}
            <i className="fas fa-chevron-right ml-2"></i>
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuizDisplay;
