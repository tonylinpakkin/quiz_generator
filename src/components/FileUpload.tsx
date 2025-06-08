import React, { useState, useRef } from 'react';
import { FileInfo, QuizGenerationRequest } from '../types';
import LoadingSpinner from './LoadingSpinner';

interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  onGenerateQuiz: (fileId: string, options: Partial<QuizGenerationRequest>) => Promise<void>;
  files: FileInfo[];
  error: string | null;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileUpload,
  onGenerateQuiz,
  files,
  error
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [showQuizOptions, setShowQuizOptions] = useState(false);
  const [quizOptions, setQuizOptions] = useState({
    num_questions: 5,
    question_types: ['multiple_choice'],
    difficulty_level: 'medium',
    focus_topics: []
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelection = async (file: File) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.txt'];

    const isValidType = allowedTypes.includes(file.type) || 
      allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
      alert('Please upload a PDF, DOCX, or TXT file.');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB.');
      return;
    }

    await onFileUpload(file);
  };

  const [isLoading, setIsLoading] = useState(false);

  const handleGenerateQuiz = async () => {
    if (!selectedFile) return;
    try {
      setIsLoading(true);
      await onGenerateQuiz(selectedFile, quizOptions);
      setShowQuizOptions(false);
    } catch (error: any) {
      console.error("Failed to generate quiz:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename: string) => {
    const extension = filename.toLowerCase().split('.').pop();
    switch (extension) {
      case 'pdf':
        return 'fas fa-file-pdf text-red-500';
      case 'docx':
        return 'fas fa-file-word text-blue-500';
      case 'txt':
        return 'fas fa-file-alt text-gray-500';
      default:
        return 'fas fa-file text-gray-500';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner message="Generating quiz..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* File Upload Area */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Study Material</h2>

        <div
          className={`file-upload-area ${dragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="space-y-4">
            <i className="fas fa-cloud-upload-alt text-4xl text-gray-400"></i>
            <div>
              <p className="text-lg font-medium text-gray-900">
                Drop your file here or click to browse
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Supports PDF, DOCX, and TXT files up to 10MB
              </p>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.txt"
            onChange={handleFileInput}
          />
        </div>
      </div>

      {/* Uploaded Files */}
      {files.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Files</h3>

          <div className="space-y-3">
            {files.map((file) => (
              <div
                key={file.file_id}
                className={`flex items-center justify-between p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedFile === file.file_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedFile(file.file_id)}
              >
                <div className="flex items-center space-x-3">
                  <i className={getFileIcon(file.filename)}></i>
                  <div>
                    <p className="font-medium text-gray-900">{file.filename}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{formatFileSize(file.file_size)}</span>
                      <span>{new Date(file.upload_time).toLocaleDateString()}</span>
                      {file.text_extracted && (
                        <span className="text-green-600">
                          <i className="fas fa-check mr-1"></i>
                          Text extracted ({file.word_count} words)
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {file.text_extracted && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(file.file_id);
                        setShowQuizOptions(true);
                      }}
                      className="btn-primary text-sm"
                    >
                      <i className="fas fa-brain mr-1"></i>
                      Generate Quiz
                    </button>
                  )}

                  {selectedFile === file.file_id && (
                    <i className="fas fa-check-circle text-blue-500"></i>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quiz Generation Options */}
      {showQuizOptions && selectedFile && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quiz Options</h3>

          <div className="grid gap-4">
           <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Questions
              </label>
              <select
                className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                value={quizOptions.num_questions}
                onChange={(e) =>
                  setQuizOptions({
                    ...quizOptions,
                    num_questions: parseInt(e.target.value, 10),
                  })
                }
              >
                <option value="3">3 Questions</option>
                <option value="5" selected>5 Questions</option>
                <option value="8">8 Questions</option>
                <option value="10">10 Questions</option>
              </select>
            </div>



            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Question Types
              </label>
              <div className="flex flex-wrap gap-3">
                {[
                  { value: 'multiple_choice', label: 'Multiple Choice' },
                  { value: 'true_false', label: 'True/False' }
                ].map((type) => (
                  <label key={type.value} className="flex items-center">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={quizOptions.question_types.includes(type.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setQuizOptions({
                            ...quizOptions,
                            question_types: [...quizOptions.question_types, type.value]
                          });
                        } else {
                          setQuizOptions({
                            ...quizOptions,
                            question_types: quizOptions.question_types.filter(t => t !== type.value)
                          });
                        }
                      }}
                    />
                    <span className="ml-2 text-sm text-gray-700">{type.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowQuizOptions(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleGenerateQuiz}
              className="btn-primary"
              disabled={quizOptions.question_types.length === 0}
            >
              <i className="fas fa-magic mr-2"></i>
              Generate Quiz
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
