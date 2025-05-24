export enum FileType {
  PDF = 'pdf',
  DOCX = 'docx',
  TXT = 'txt'
}

export enum QuestionType {
  MULTIPLE_CHOICE = 'multiple_choice',
  TRUE_FALSE = 'true_false',
  SHORT_ANSWER = 'short_answer'
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface FileInfo {
  file_id: string;
  filename: string;
  file_type: FileType;
  file_size: number;
  upload_time: string;
  text_extracted: boolean;
  word_count?: number;
}

export interface QuizQuestion {
  id: string;
  question: string;
  question_type: QuestionType;
  options?: string[];
  correct_answer: string;
  explanation?: string;
  difficulty?: string;
}

export interface Quiz {
  id: string;
  title: string;
  description?: string;
  source_file_id: string;
  questions: QuizQuestion[];
  created_at: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

export interface QuizGenerationRequest {
  file_id: string;
  num_questions: number;
  question_types: string[];
  difficulty_level: string;
  focus_topics?: string[];
}

export interface QuizGenerationResponse {
  quiz_id: string;
  status: ProcessingStatus;
  message: string;
  quiz?: Quiz;
}

export interface QuizUpdateRequest {
  title?: string;
  description?: string;
  questions?: QuizQuestion[];
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  file_type: FileType;
  file_size: number;
  status: ProcessingStatus;
  message: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface TextExtractionResult {
  file_id: string;
  text_content: string;
  word_count: number;
  extraction_time: number;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Hook types
export interface UseQuizResult {
  quizzes: Quiz[];
  loading: boolean;
  error: string | null;
  loadQuizzes: () => Promise<void>;
  generateQuiz: (request: QuizGenerationRequest) => Promise<Quiz>;
  updateQuiz: (quizId: string, updates: QuizUpdateRequest) => Promise<Quiz>;
  deleteQuiz: (quizId: string) => Promise<void>;
  duplicateQuiz: (quizId: string) => Promise<Quiz>;
}

export interface UseFileResult {
  files: FileInfo[];
  loading: boolean;
  error: string | null;
  loadFiles: () => Promise<void>;
  uploadFile: (file: File) => Promise<UploadResponse>;
  deleteFile: (fileId: string) => Promise<void>;
  getExtractedText: (fileId: string) => Promise<TextExtractionResult>;
}

// Component prop types
export interface QuizDisplayProps {
  quiz: Quiz;
  onEdit: () => void;
  onDelete: () => void;
  onBack: () => void;
}

export interface QuizEditorProps {
  quiz: Quiz;
  onSave: (updates: QuizUpdateRequest) => void;
  onCancel: () => void;
}

export interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  onGenerateQuiz: (fileId: string, options: Partial<QuizGenerationRequest>) => Promise<void>;
  files: FileInfo[];
  error: string | null;
}

export interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}
