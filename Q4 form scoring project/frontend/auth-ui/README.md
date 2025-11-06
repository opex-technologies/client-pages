# Authentication UI

React-based authentication interface for the Form Builder & Response Scoring System.

Created: November 5, 2025

## Features

- User Registration with real-time password strength indicator
- User Login with email/password authentication
- Protected Routes with automatic redirection
- JWT Token Management with automatic refresh
- Session Persistence across page reloads
- Form Validation matching backend requirements
- Responsive Design with Tailwind CSS

## Tech Stack

- React 19 - UI framework
- Vite - Build tool and dev server
- React Router - Client-side routing
- Tailwind CSS - Utility-first styling
- JWT - Token-based authentication

## Quick Start

```bash
# Install dependencies
npm install

# Create .env file from example
cp .env.example .env

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

## Configuration

Create a `.env.local` file for development:

```bash
# Development (local)
VITE_API_BASE_URL=http://localhost:8080
```

For production deployment, the `.env.production` file is already configured:

```bash
# Production (deployed Cloud Function)
VITE_API_BASE_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
```

### ⚠️ Known Issue: BigQuery Streaming Buffer Limitation

The deployed authentication API currently uses BigQuery for data storage, which has a streaming buffer limitation:
- **Registration works** - New users can be created
- **Login fails for new users** - Cannot update user data within 90 minutes of registration

**Solution**: Migrate authentication data to Firestore or Cloud SQL. See `backend/auth/BIGQUERY_LIMITATIONS.md` for detailed migration plan.

## Project Structure

```
src/
├── contexts/AuthContext.jsx      # Authentication state
├── services/authService.js       # API calls
├── pages/                        # Page components
├── utils/validation.js           # Form validation
├── config.js                     # App configuration
└── App.jsx                       # Main routing
```

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

## Deployment

```bash
npm run build     # Build for production
npm run deploy    # Deploy to GitHub Pages
```

## License

Proprietary - Opex Technologies
