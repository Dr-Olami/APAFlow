# SMEFlow Development Environment

A comprehensive development setup for building LLM applications with LangChain, LangGraph, and Flowise integration.

## 🚀 Features

- **Python Environment**: LangChain, LangGraph, and Jupyter support
- **JavaScript/TypeScript**: ESLint, Prettier, and React snippets for Flowise
- **Docker/Kubernetes**: Full containerization support with YAML/JSON tooling
- **Observability**: Langfuse integration for LLM call tracing
- **Security**: CodeQL vulnerability scanning with Keycloak/Cerbos support
- **Task Management**: VS Code tasks integration

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- uv (fast Python package installer)
- Docker (optional)
- VS Code with recommended extensions

## 🛠️ Setup

### 1. Python Environment
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies with uv (faster)
uv pip install -r requirements.txt

# Or use traditional pip
pip install -r requirements.txt
```

### 2. JavaScript/TypeScript
```bash
# Install Node dependencies
npm install
```

### 3. Environment Variables
```bash
# Copy and configure environment variables
cp .env.example .env
```

## 🔧 VS Code Extensions

Install the recommended extensions from `.vscode/extensions.json`:

- Docker
- Kubernetes Tools
- YAML/JSON support
- ESLint & Prettier
- Python & Jupyter
- CodeQL
- Todoist

## 🏃‍♂️ Quick Start

### Start Jupyter Notebook
```bash
jupyter notebook
```

### Run Flowise Development
```bash
npm run dev
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🔍 Code Quality

### Linting
```bash
npx eslint . --ext .js,.jsx,.ts,.tsx
```

### Formatting
```bash
npx prettier --write .
```

### Security Scanning
CodeQL analysis runs automatically on push to main branch.

## 📊 Observability

Configure Langfuse in your `.env` file:
```env
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## 🔐 Security

### Keycloak Integration
See `security/keycloak-security.py` for JWT token validation.

### Cerbos Authorization
See `security/cerbos-policy.py` for fine-grained permissions.

## 📝 Code Snippets

Use the Flowise React snippets in VS Code:
- `flowise-node`: Create custom Flowise node
- `flowise-chain`: Create LangChain integration
- `flowise-tool`: Create custom tool

## 🤝 Contributing

1. Follow the ESLint and Prettier configurations
2. Ensure all tests pass
3. Security scan with CodeQL before merging
