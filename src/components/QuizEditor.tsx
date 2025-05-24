import React, { useState } from 'react';
import { Quiz, QuizQuestion, QuestionType } from '../types';

interface QuizEditorProps {
  quiz: Quiz;
  onSave: (updates: any) => void;
  onCancel: () => void;
}

const QuizEditor: React.FC<QuizEditorProps> = ({ quiz, onSave, onCancel }) => {
  const [title, setTitle] = useState(quiz.title);
  const [description, setDescription] = useState(quiz.description || '');
  const [questions, setQuestions] = useState<QuizQuestion[]>([...quiz.questions]);
  const [editingQuestion, setEditingQuestion] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const markChanged = () => {
    if (!hasChanges) setHasChanges(true);
  };

  const handleTitleChange = (newTitle: string) => {
    setTitle(newTitle);
    markChanged();
  };

  const handleDescriptionChange = (newDescription: string) => {
    setDescription(newDescription);
    markChanged();
  };

  const updateQuestion = (questionId: string, updates: Partial<QuizQuestion>) => {
    setQuestions(prev => prev.map(q => 
      q.id === questionId ? { ...q, ...updates } : q
    ));
    markChanged();
  };

  const addQuestion = () => {
    const newQuestion: QuizQuestion = {
      id: `q_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      question: 'New question',
      question_type: QuestionType.MULTIPLE_CHOICE,
      options: ['Option A', 'Option B', 'Option C', 'Option D'],
      correct_answer: 'Option A',
      explanation: '',
      difficulty: 'medium'
    };

    setQuestions(prev => [...prev, newQuestion]);
    setEditingQuestion(newQuestion.id);
    markChanged();
  };

  const deleteQuestion = (questionId: string) => {
    if (questions.length <= 1) {
      alert('Quiz must have at least one question');
      return;
    }
    
    if (window.confirm('Are you sure you want to delete this question?')) {
      setQuestions(prev => prev.filter(q => q.id !== questionId));
      if (editingQuestion === questionId) {
        setEditingQuestion(null);
      }
      markChanged();
    }
  };

  const moveQuestion = (questionId: string, direction: 'up' | 'down') => {
    const currentIndex = questions.findIndex(q => q.id === questionId);
    if (
      (direction === 'up' && currentIndex === 0) ||
      (direction === 'down' && currentIndex === questions.length - 1)
    ) {
      return;
    }

    const newQuestions = [...questions];
    const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    [newQuestions[currentIndex], newQuestions[targetIndex]] = 
    [newQuestions[targetIndex], newQuestions[currentIndex]];
    
    setQuestions(newQuestions);
    markChanged();
  };

  const handleSave = () => {
    const updates = {
      title,
      description,
      questions
    };
    onSave(updates);
  };

  const handleCancel = () => {
    if (hasChanges && !window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
      return;
    }
    onCancel();
  };

  const renderQuestionEditor = (question: QuizQuestion, index: number) => {
    const isEditing = editingQuestion === question.id;

    return (
      <div key={question.id} className="card">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center space-x-2">
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded">
              Q{index + 1}
            </span>
            <select
              className="select-field text-sm"
              value={question.question_type}
              onChange={(e) => {
                const newType = e.target.value as QuestionType;
                let newOptions = question.options;
                let newAnswer = question.correct_answer;

                if (newType === QuestionType.TRUE_FALSE) {
                  newOptions = ['True', 'False'];
                  newAnswer = 'True';
                } else if (newType === QuestionType.SHORT_ANSWER) {
                  newOptions = undefined;
                } else if (newType === QuestionType.MULTIPLE_CHOICE && !newOptions) {
                  newOptions = ['Option A', 'Option B', 'Option C', 'Option D'];
                  newAnswer = 'Option A';
                }

                updateQuestion(question.id, {
                  question_type: newType,
                  options: newOptions,
                  correct_answer: newAnswer
                });
              }}
            >
              <option value="multiple_choice">Multiple Choice</option>
              <option value="true_false">True/False</option>
              <option value="short_answer">Short Answer</option>
            </select>
            <select
              className="select-field text-sm"
              value={question.difficulty}
              onChange={(e) => updateQuestion(question.id, { difficulty: e.target.value })}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => moveQuestion(question.id, 'up')}
              disabled={index === 0}
              className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50"
            >
              <i className="fas fa-chevron-up"></i>
            </button>
            <button
              onClick={() => moveQuestion(question.id, 'down')}
              disabled={index === questions.length - 1}
              className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50"
            >
              <i className="fas fa-chevron-down"></i>
            </button>
            <button
              onClick={() => setEditingQuestion(isEditing ? null : question.id)}
              className="p-1 text-blue-600 hover:text-blue-800"
            >
              <i className={`fas ${isEditing ? 'fa-check' : 'fa-edit'}`}></i>
            </button>
            <button
              onClick={() => deleteQuestion(question.id)}
              className="p-1 text-red-600 hover:text-red-800"
            >
              <i className="fas fa-trash"></i>
            </button>
          </div>
        </div>

        {/* Question Text */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Question
          </label>
          {isEditing ? (
            <textarea
              className="textarea-field"
              rows={2}
              value={question.question}
              onChange={(e) => updateQuestion(question.id, { question: e.target.value })}
            />
          ) : (
            <p className="text-gray-900">{question.question}</p>
          )}
        </div>

        {/* Options */}
        {(question.question_type === QuestionType.MULTIPLE_CHOICE || 
          question.question_type === QuestionType.TRUE_FALSE) && question.options && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Options
            </label>
            <div className="space-y-2">
              {question.options.map((option, optionIndex) => (
                <div key={optionIndex} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name={`correct-${question.id}`}
                    checked={question.correct_answer === option}
                    onChange={() => updateQuestion(question.id, { correct_answer: option })}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  {isEditing && question.question_type === QuestionType.MULTIPLE_CHOICE ? (
                    <input
                      type="text"
                      className="input-field flex-1"
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...question.options!];
                        newOptions[optionIndex] = e.target.value;
                        updateQuestion(question.id, { options: newOptions });
                        
                        // Update correct answer if it was this option
                        if (question.correct_answer === option) {
                          updateQuestion(question.id, { correct_answer: e.target.value });
                        }
                      }}
                    />
                  ) : (
                    <span className="flex-1">{option}</span>
                  )}
                  <span className="text-xs text-gray-500">
                    {question.correct_answer === option ? 'Correct' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Correct Answer for Short Answer */}
        {question.question_type === QuestionType.SHORT_ANSWER && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suggested Answer
            </label>
            {isEditing ? (
              <textarea
                className="textarea-field"
                rows={2}
                value={question.correct_answer}
                onChange={(e) => updateQuestion(question.id, { correct_answer: e.target.value })}
              />
            ) : (
              <p className="text-gray-900">{question.correct_answer}</p>
            )}
          </div>
        )}

        {/* Explanation */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Explanation (Optional)
          </label>
          {isEditing ? (
            <textarea
              className="textarea-field"
              rows={2}
              value={question.explanation || ''}
              onChange={(e) => updateQuestion(question.id, { explanation: e.target.value })}
              placeholder="Provide an explanation for the answer..."
            />
          ) : (
            <p className="text-gray-600">{question.explanation || 'No explanation provided'}</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleCancel}
            className="text-gray-600 hover:text-gray-800"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            Back
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Edit Quiz</h1>
          {hasChanges && (
            <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
        </div>
        
        <div className="flex space-x-3">
          <button onClick={handleCancel} className="btn-secondary">
            Cancel
          </button>
          <button 
            onClick={handleSave}
            className="btn-primary"
            disabled={!hasChanges}
          >
            <i className="fas fa-save mr-2"></i>
            Save Changes
          </button>
        </div>
      </div>

      {/* Quiz Metadata */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quiz Information</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title
            </label>
            <input
              type="text"
              className="input-field"
              value={title}
              onChange={(e) => handleTitleChange(e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              className="textarea-field"
              rows={2}
              value={description}
              onChange={(e) => handleDescriptionChange(e.target.value)}
              placeholder="Describe this quiz..."
            />
          </div>
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">
            Questions ({questions.length})
          </h2>
          <button onClick={addQuestion} className="btn-primary">
            <i className="fas fa-plus mr-2"></i>
            Add Question
          </button>
        </div>

        {questions.map((question, index) => renderQuestionEditor(question, index))}
      </div>
    </div>
  );
};

export default QuizEditor;
