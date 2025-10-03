# Project Specifications

## Project Overview
Building a form builder and response scoring system with supporting database infrastructure.

## Database Tables

### Source Tables
1. **Provider Table**
   - `id` - Primary key
   - `category` - Provider category
   - `name` - Provider name
   - `logo_url` - URL to provider logo
   - `created_at` - Timestamp
   - `updated_at` - Timestamp

2. **Question Table**
   - `id` - Primary key
   - `category` - Question category
   - `text` - Question text
   - `default_weight` - Default weight for scoring
   - `tags` - Question tags
   - `created_at` - Timestamp
   - `updated_at` - Timestamp

3. **Client Table**
   - `id` - Primary key
   - `category` - Client category
   - `name` - Client name
   - `logo_url` - URL to client logo
   - `created_at` - Timestamp
   - `updated_at` - Timestamp

### Utility Tables
1. **Users Table**
   - `id` - Primary key
   - `email` - User email (unique)
   - `password_hash` - Bcrypt hashed password
   - `created_at` - Timestamp
   - `last_login` - Timestamp

2. **Permission Groups Table**
   - `id` - Primary key
   - `user_id` - Foreign key to Users table
   - `company` - Company access (null = all)
   - `category` - Category access (null = all)
   - `permission_level` - 'view', 'edit', 'admin'
   - `created_at` - Timestamp

## User Interfaces

### 1. Form Builder
- **Functionality**:
  - Repopulate questions from entire categories or individual questions
  - Create new questions by modifying existing ones
  - Generate standalone HTML forms similar to existing survey forms
  - Automatically deploy generated forms to GitHub Pages
- **Features**:
  - Category-based question selection
  - Question modification capabilities
  - Section organization within single-page forms
  - HTML form generation with embedded JavaScript
  - Form preview before deployment
  - Automatic form submission to existing webhook (`https://opex-form-webhook-4jypryamoq-uc.a.run.app`)
  - GitHub integration for automatic form deployment
- **Output**:
  - Static HTML files with Opex branding (logo from Cloud Storage)
  - Embedded form submission logic
  - Dynamic question generation based on selected categories
  - Responsive design matching existing forms

### 2. Response Scorer
- **Data Source**: `opex-data-lake-k23k4y98m.scoring.all_survey_responses` view
- **Filtering Options**:
  - Contact company
  - Source (form name)
  - Timestamp
  - Scored/unscored status
- **Functionality**:
  - Display questions with prepopulated weight values
  - Score input boxes for each question
  - Details/notes text area for each question
  - Submit scored responses to materialized table
  - Edit previously scored responses with prepopulated scores/weights/details
  - Resubmit updated scores

## Architecture

### Backend Services
1. **Cloud Functions** (Python 3.10+)
   - `form-builder-api` - Handles CRUD operations for questions, providers, and clients
   - `response-scorer-api` - Manages scoring operations and score persistence
   - `auth-api` - Handles authentication and permission management

2. **Data Storage**
   - **BigQuery** - All tables (Provider, Question, Client, survey responses, scoring data)
   - **Cloud Storage** - Static asset hosting (logos, etc.)
   - **Dataset**: `opex_dev` (same as existing project)

3. **API Management**
   - **API Gateway** or **Cloud Endpoints** - Centralized API management with authentication
   - RESTful API design with proper versioning

4. **Authentication & Authorization**
   - **BigQuery-based Authentication**:
     - `users` table: {id, email, password_hash, created_at, last_login}
     - Login form on both UIs (Form Builder and Response Scorer)
     - JWT tokens issued by auth Cloud Function
     - Token stored in browser localStorage/sessionStorage
     - Token sent with each API request in Authorization header
   - **Permission System**:
     - Permission groups table determines access levels
     - Middleware in Cloud Functions validates permissions per request

### Frontend
- **Hosting**: GitHub Pages (static site hosting)
- **Framework**: React/Vue.js for interactive UIs (built as static assets)
- **Build Process**: GitHub Actions for automated deployment
- **State Management**: Redux/Vuex for complex form states
- **API Integration**: Axios/Fetch for backend communication

### Data Flow
```
User → Login Page → auth-api → Validate credentials → Issue JWT
           ↓
    Store JWT in browser
           ↓
Form Builder UI → API Gateway → form-builder-api → BigQuery
  (JWT in header)                        ↓
                              Generate HTML form
                                         ↓
                        GitHub API → Deploy to GitHub Pages
                                         ↓
                   Generated Form → Existing webhook → BigQuery

Response Scorer UI → API Gateway → response-scorer-api → BigQuery
  (JWT in header)

All API calls: JWT validation → Permission check → Execute request
```

## Technical Requirements
- Single BigQuery dataset (`opex_dev`) for all data storage
- SQL-based CRUD operations for all tables
- HTML form generation matching existing survey format
- GitHub API integration for automated form deployment
- Form templates based on existing Web/surveys/ structure
- Automatic webhook endpoint configuration
- Transaction support using BigQuery's DML statements
- Row-level security based on permission groups
- API rate limiting and monitoring
- Error handling and retry logic
- Comprehensive logging in Cloud Logging
- Optimized for ~100 submissions/week volume

## Development Considerations
- Use service accounts for inter-service communication
- Implement proper CORS handling for web UIs
- Version control for API changes
- Automated testing for Cloud Functions
- CI/CD pipeline using Cloud Build
- Environment separation (dev/staging/prod)

## Success Criteria
- Functional form builder with real-time category-based question management
- Complete response scoring workflow with edit capabilities
- Robust permission system with granular access controls
- Sub-second response times for UI operations
- 99.9% uptime for critical services
- Comprehensive audit trail for all operations

## Project Estimate

Based on the original project billing of $8,500, this project is estimated at **$16,500** due to increased complexity:

| Component | Hours | Rate | Total |
|-----------|-------|------|-------|
| **Backend Development** | | | |
| Authentication System (JWT, login) | 24 | $75 | $1,800 |
| Form Builder API (CRUD operations) | 32 | $75 | $2,400 |
| Response Scorer API | 24 | $75 | $1,800 |
| BigQuery Schema & Tables | 16 | $75 | $1,200 |
| **Frontend Development** | | | |
| Form Builder UI | 48 | $75 | $3,600 |
| Response Scorer UI | 40 | $75 | $3,000 |
| Login/Auth UI Components | 16 | $40 | $640 |
| **Integration & Deployment** | | | |
| GitHub API Integration | 16 | $75 | $1,200 |
| API Gateway Setup | 8 | $75 | $600 |
| Testing & Documentation | 12 | $40 | $480 |
| **Total Development** | **236** | | **$16,720** |

**Rounded Project Total: $16,500**

### Comparison to Original Project
- Original: Mostly static forms with simple webhook
- This project: Full web applications with authentication, CRUD operations, and complex workflows
- ~2x complexity = ~2x cost