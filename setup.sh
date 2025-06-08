#!/bin/bash

# Quiz Generator Setup Script
# This script sets up the development environment for the Quiz Generator application

set -e  # Exit on any error

echo "🧠 Quiz Generator Setup"
echo "======================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        
        # Check if version is 3.8+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python version is compatible (3.8+)"
        else
            print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Check if Node.js is installed
check_node() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION found"
        
        # Check if version is 16+
        if node -e "process.exit(parseInt(process.version.slice(1)) >= 16 ? 0 : 1)"; then
            print_success "Node.js version is compatible (16+)"
        else
            print_error "Node.js 16+ is required. Current version: $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    print_status "Checking npm installation..."
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm $NPM_VERSION found"
    else
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
}

# Create virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install fastapi uvicorn python-multipart
    pip install PyMuPDF python-docx
    pip install httpx pydantic
    pip install python-dotenv
    
    print_success "Python dependencies installed"
}

# Install Node.js dependencies
setup_node_env() {
    print_status "Installing Node.js dependencies..."
    
    npm install react react-dom
    npm install --save-dev @types/react @types/react-dom
    npm install --save-dev @vitejs/plugin-react vite typescript
    npm install axios
    npm install --save-dev tailwindcss postcss autoprefixer
    npm install --save-dev @types/node
    
    print_success "Node.js dependencies installed"
}

# Create environment file
setup_env_file() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file to configure your settings"
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads
    mkdir -p dist
    mkdir -p logs
    
    print_success "Directories created"
}

# Setup database (for future PostgreSQL support)
setup_database() {
    print_status "Database setup..."
    
    # Check if PostgreSQL environment variables are set
    if [ -n "$DATABASE_URL" ] || [ -n "$PGDATABASE" ]; then
        print_success "PostgreSQL configuration detected"
        print_warning "Make sure PostgreSQL is running and accessible"
    else
        print_warning "No PostgreSQL configuration found, using in-memory storage"
        print_warning "For production, configure PostgreSQL environment variables"
    fi
}

# Build frontend
build_frontend() {
    print_status "Building frontend..."
    
    npm run build
    
    if [ $? -eq 0 ]; then
        print_success "Frontend built successfully"
    else
        print_error "Frontend build failed"
        exit 1
    fi
}

# Main setup function
main() {
    echo
    print_status "Starting Quiz Generator setup..."
    echo
    
    # Check prerequisites
    check_python
    check_node
    check_npm
    
    echo
    print_status "Prerequisites check passed!"
    echo
    
    # Setup environments
    setup_python_env
    echo
    setup_node_env
    echo
    
    # Setup configuration
    setup_env_file
    create_directories
    setup_database
    echo
    
    # Build application
    build_frontend
    echo
    
    print_success "Setup completed successfully!"
    echo
    echo "🚀 Next steps:"
    echo "1. Review and edit .env file if needed"
    echo "2. Set LLM_MOCK_MODE=false in .env"
    echo "3. Start the application:"
    echo "   - Backend: source venv/bin/activate && python main.py"
    echo "   - Frontend: npm run dev (in another terminal)"
    echo "4. Open http://localhost:5000 in your browser"
    echo
    echo "📚 For more information, see README.md"
}

# Run main function
main "$@"
