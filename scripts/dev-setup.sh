#!/bin/bash

# FireFeed API Development Setup Script
# This script sets up the development environment for FireFeed API

set -e

echo "🚀 Setting up FireFeed API development environment..."

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

# Check if Python 3.11 is installed
check_python() {
    print_status "Checking Python version..."
    if ! command -v python3.11 &> /dev/null; then
        print_error "Python 3.11 is required but not installed."
        print_status "Please install Python 3.11 and try again."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3.11 --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Production dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    else
        print_warning "requirements-dev.txt not found"
    fi
}

# Setup environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    if [ ! -f "./firefeed-api/.env" ]; then
        if [ -f "./firefeed-api/.env.example" ]; then
            cp ./firefeed-api/.env.example ./firefeed-api/.env
            print_success "Environment file created from template"
            print_warning "Please update ./firefeed-api/.env file with your configuration"
        else
            print_warning "./firefeed-api/.env.example not found, creating basic .env file"
            cat > ./firefeed-api/.env << EOF
# Database Configuration
FIREFEED_DB_HOST=localhost
FIREFEED_DB_PORT=5432
FIREFEED_DB_NAME=firefeed_dev
FIREFEED_DB_USER=firefeed_user
FIREFEED_DB_PASSWORD=your_password_here

# Redis Configuration
FIREFEED_REDIS_HOST=localhost
FIREFEED_REDIS_PORT=6379
FIREFEED_REDIS_DB=0

# JWT Configuration
FIREFEED_JWT_SECRET_KEY=your-secret-key-here
FIREFEED_JWT_ALGORITHM=HS256
FIREFEED_JWT_EXPIRE_MINUTES=30

# Internal API Configuration
FIREFEED_INTERNAL_API_URL=http://localhost:8001
FIREFEED_INTERNAL_SERVICE_TOKEN=your-service-token-here

# Email Configuration
FIREFEED_EMAIL_HOST=smtp.example.com
FIREFEED_EMAIL_PORT=587
FIREFEED_EMAIL_USER=your-email@example.com
FIREFEED_EMAIL_PASSWORD=your-email-password
FIREFEED_EMAIL_FROM=FireFeed <no-reply@firefeed.net>

# Translation Configuration
FIREFEED_TRANSLATION_MODEL_PATH=/path/to/translation/model
FIREFEED_TRANSLATION_CACHE_SIZE=1000
FIREFEED_TRANSLATION_CACHE_TTL=3600

# Logging Configuration
FIREFEED_LOG_LEVEL=INFO
FIREFEED_LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Development Configuration
FIREFEED_DEBUG=True
FIREFEED_RELOAD=True
FIREFEED_HOST=0.0.0.0
FIREFEED_PORT=8000
EOF
            print_success "Basic .env file created"
        fi
    else
        print_warning "./firefeed-api/.env file already exists"
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_warning "Docker is not running. Please start Docker and run the database setup manually."
        print_status "You can use: docker-compose up -d postgres"
        return 1
    fi
    
    # Start PostgreSQL
    print_status "Starting PostgreSQL..."
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Run database migrations
    if [ -f "database/migrations.sql" ]; then
        print_status "Running database migrations..."
        docker-compose exec -T postgres psql -U firefeed_user -d firefeed_dev -f /app/database/migrations.sql
        print_success "Database migrations completed"
    else
        print_warning "No migration file found"
    fi
}

# Setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    # Start Redis
    docker-compose up -d redis
    
    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    sleep 5
    
    # Test Redis connection
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        print_success "Redis is ready"
    else
        print_warning "Redis might not be ready yet"
    fi
}

# Run code quality checks
run_quality_checks() {
    print_status "Running code quality checks..."
    
    # Run Black
    if command -v black &> /dev/null; then
        black --check .
        print_success "Black formatting check passed"
    else
        print_warning "Black not found, skipping formatting check"
    fi
    
    # Run isort
    if command -v isort &> /dev/null; then
        isort --check-only .
        print_success "Import sorting check passed"
    else
        print_warning "isort not found, skipping import sorting check"
    fi
    
    # Run Flake8
    if command -v flake8 &> /dev/null; then
        flake8 .
        print_success "Linting check passed"
    else
        print_warning "Flake8 not found, skipping linting check"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Run pytest
    if command -v pytest &> /dev/null; then
        pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Create development scripts
create_dev_scripts() {
    print_status "Creating development scripts..."
    
    # Create run script
    cat > run-dev.sh << 'EOF'
#!/bin/bash
# Development server startup script

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ./firefeed-api/.env ]; then
    export $(cat ./firefeed-api/.env | grep -v '^#' | xargs)
fi

# Start the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
EOF
    chmod +x run-dev.sh
    print_success "Development server script created (run-dev.sh)"
    
    # Create test script
    cat > run-tests.sh << 'EOF'
#!/bin/bash
# Test runner script

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ./firefeed-api/.env ]; then
    export $(cat ./firefeed-api/.env | grep -v '^#' | xargs)
fi

# Run tests
pytest tests/ -v --cov=firefeed_api --cov-report=html --cov-report=term
EOF
    chmod +x run-tests.sh
    print_success "Test runner script created (run-tests.sh)"
    
    # Create lint script
    cat > run-lint.sh << 'EOF'
#!/bin/bash
# Code quality check script

# Activate virtual environment
source venv/bin/activate

# Run code quality checks
echo "Running Black..."
black .

echo "Running isort..."
isort .

echo "Running Flake8..."
flake8 .

echo "Running MyPy..."
mypy firefeed_api/

echo "All code quality checks completed!"
EOF
    chmod +x run-lint.sh
    print_success "Lint script created (run-lint.sh)"
}

# Main setup function
main() {
    echo "Starting FireFeed API development setup..."
    
    # Check prerequisites
    check_python
    
    # Setup virtual environment
    setup_venv
    
    # Install dependencies
    install_dependencies
    
    # Setup environment
    setup_env
    
    # Setup services
    setup_database
    setup_redis
    
    # Run quality checks
    run_quality_checks
    
    # Run tests
    run_tests
    
    # Create development scripts
    create_dev_scripts
    
    print_success "🎉 FireFeed API development environment setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Update ./firefeed-api/.env file with your configuration"
    echo "2. Run './run-dev.sh' to start the development server"
    echo "3. Run './run-tests.sh' to run tests"
    echo "4. Run './run-lint.sh' to check code quality"
    echo ""
    echo "For more information, see the README.md file."
}

# Run main function
main "$@"