# Q4 Form Scoring Project - Detailed Implementation Plan

**Project:** Form Builder & Response Scoring System
**Client:** Opex Technologies
**Duration:** 9 weeks
**Total Tasks:** 200+ individual tasks
**Prepared:** November 1, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Architecture Overview](#project-architecture-overview)
3. [Phase 1: Infrastructure & Authentication](#phase-1-infrastructure--authentication-weeks-1-2)
4. [Phase 2: Form Builder Development](#phase-2-form-builder-development-weeks-3-4)
5. [Phase 3: Response Scorer Development](#phase-3-response-scorer-development-weeks-5-6)
6. [Phase 4: Integration & Testing](#phase-4-integration--testing-weeks-7-8)
7. [Phase 5: Deployment & Training](#phase-5-deployment--training-week-9)
8. [Dependencies & Critical Path](#dependencies--critical-path)
9. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

This implementation plan breaks down the Form Builder & Response Scoring System into **200+ granular tasks** sequenced for maximum efficiency. The plan builds upon existing production infrastructure (webhook, BigQuery, 14 HTML forms) and adds three greenfield components: Authentication System, Form Builder Application, and Response Scorer Application.

**Key Strategy:**
- Extend existing infrastructure, don't replace
- Build authentication foundation first (blocks all other work)
- Develop Form Builder and Response Scorer in parallel after auth
- Maintain backward compatibility with existing forms
- Zero-downtime deployment

**Critical Path:** Authentication → Database Schema → API Development → UI Development → Integration

---

## Project Architecture Overview

### Current State
```
Question DB (CSV) → [Manual HTML Coding] → 14 Static Forms → Webhook → BigQuery
                                                                    ↓
                                                      Google Sheets (Manual Scoring)
```

### Target State
```
                     ┌─── Form Builder App ───┐
                     │  - Select questions    │
                     │  - Set weights         │
Question DB ────────→│  - Preview form        │──→ GitHub Pages ──→ Static Form
(BigQuery)           │  - Deploy to GitHub    │                       ↓
                     └────────────────────────┘                  Webhook (existing)
                                                                       ↓
                     ┌─── Response Scorer ────┐                  BigQuery
                     │  - View responses      │                       ↓
Users → Login ──────→│  - Filter/search       │←──────────────────────┘
     (JWT Auth)      │  - Score & comment     │
                     │  - Audit trail         │
                     └────────────────────────┘
```

### Tech Stack

**Frontend:**
- React.js (Form Builder & Response Scorer SPAs)
- Vite for build tooling
- Tailwind CSS for styling
- Hosted on GitHub Pages

**Backend:**
- Python 3.10+ Cloud Functions
- API Gateway for routing & auth
- JWT for authentication
- BigQuery for data storage

**Infrastructure:**
- GCP Project: `opex-data-lake-k23k4y98m`
- Existing webhook: `https://opex-form-webhook-4jypryamoq-uc.a.run.app`
- Cloud Storage: `opex-web-forms-20250716-145646`
- GitHub: Deploy static forms automatically

---

## Phase 1: Infrastructure & Authentication (Weeks 1-2)

**Objective:** Build authentication foundation and extend BigQuery schema

**Hours:** 64 hours
**Cost:** $4,240
**Blocking Factor:** HIGH - All other phases depend on auth completion

---

### Week 1: Database Schema & Core Infrastructure

#### Task Group 1.1: BigQuery Schema Design (Day 1, 6 hours)

**1.1.1** Create `/Q4 form scoring project/database/` directory structure
- Create `database/schemas/` folder
- Create `database/migrations/` folder
- Create `database/seed_data/` folder

**1.1.2** Design `auth.users` table schema
- Define columns: `user_id`, `email`, `password_hash`, `full_name`, `created_at`, `last_login`, `status`, `mfa_secret`
- Document primary keys and indexes
- Write schema SQL file: `database/schemas/auth_users.sql`
- Add comments explaining each field

**1.1.3** Design `auth.permission_groups` table schema
- Define columns: `permission_id`, `user_id`, `company`, `category`, `permission_level`, `granted_by`, `granted_at`, `expires_at`
- Define foreign key to `users` table
- Write schema SQL file: `database/schemas/auth_permission_groups.sql`
- Create enum for `permission_level`: `view`, `edit`, `admin`

**1.1.4** Design `auth.sessions` table schema
- Define columns: `session_id`, `user_id`, `jwt_token_hash`, `created_at`, `expires_at`, `ip_address`, `user_agent`, `is_active`
- Write schema SQL file: `database/schemas/auth_sessions.sql`
- Add index on `jwt_token_hash` for fast lookups

**1.1.5** Design `form_builder.form_templates` table schema
- Define columns: `template_id`, `template_name`, `opportunity_type`, `opportunity_subtype`, `questions` (ARRAY<STRUCT>), `created_by`, `created_at`, `updated_at`, `deployed_url`, `github_repo_path`, `status`, `version`
- Write schema SQL file: `database/schemas/form_templates.sql`
- Document STRUCT fields for questions: `question_id`, `weight`, `is_required`, `input_type`

**1.1.6** Design `form_builder.question_database` table schema
- Define columns: `question_id`, `question_text`, `default_weight`, `category`, `opportunity_type`, `opportunity_subtypes`, `input_type`, `validation_rules`, `help_text`, `version`, `created_at`, `updated_at`, `is_active`
- Write schema SQL file: `database/schemas/question_database.sql`
- Plan migration from existing CSV

**1.1.7** Design `scoring.scored_responses` table schema
- Define columns: `score_id`, `response_id`, `survey_type`, `company_name`, `contact_email`, `total_score`, `max_score`, `percentage`, `scored_by`, `scored_at`, `updated_at`, `notes`, `status`, `version`
- Write schema SQL file: `database/schemas/scored_responses.sql`
- Add composite index on `survey_type` + `company_name`

**1.1.8** Design `scoring.question_scores` table schema
- Define columns: `question_score_id`, `score_id`, `question`, `answer`, `weight`, `points_awarded`, `max_points`, `comments`, `scored_by`, `scored_at`
- Write schema SQL file: `database/schemas/question_scores.sql`
- Define foreign key to `scored_responses`

**1.1.9** Design `scoring.audit_trail` table schema
- Define columns: `audit_id`, `entity_type`, `entity_id`, `action`, `changed_by`, `changed_at`, `previous_value`, `new_value`, `change_reason`, `ip_address`
- Write schema SQL file: `database/schemas/audit_trail.sql`
- Add index on `entity_type` + `entity_id` for fast filtering

**1.1.10** Design `opex_dev.providers` table schema
- Define columns: `provider_id`, `category`, `name`, `logo_url`, `website`, `description`, `created_at`, `updated_at`, `is_active`
- Write schema SQL file: `database/schemas/providers.sql`

**1.1.11** Design `opex_dev.clients` table schema
- Define columns: `client_id`, `category`, `name`, `logo_url`, `contact_email`, `created_at`, `updated_at`, `is_active`
- Write schema SQL file: `database/schemas/clients.sql`

**1.1.12** Create master schema deployment script
- Write `database/deploy_schemas.py` to deploy all schemas
- Add error handling for existing tables
- Add rollback capability
- Add schema version tracking

---

#### Task Group 1.2: BigQuery Dataset Creation (Day 1, 2 hours)

**1.2.1** Create `auth` dataset in BigQuery
- Run: `bq mk --dataset --location=US opex-data-lake-k23k4y98m:auth`
- Set dataset description
- Configure access controls

**1.2.2** Create `form_builder` dataset in BigQuery
- Run: `bq mk --dataset --location=US opex-data-lake-k23k4y98m:form_builder`
- Set dataset description
- Configure access controls

**1.2.3** Verify existing datasets
- Confirm `opex_dev` dataset exists
- Confirm `scoring` dataset exists
- Document current table list

**1.2.4** Deploy all table schemas to BigQuery
- Run `python database/deploy_schemas.py`
- Verify all tables created successfully
- Document table creation timestamps

---

#### Task Group 1.3: Question Database Migration (Day 2, 6 hours)

**1.3.1** Analyze existing Question Database CSV
- Read `/Question Database(Sheet1).csv`
- Document current structure (1,042 questions)
- Identify data quality issues
- Map CSV columns to BigQuery schema

**1.3.2** Create Question Database ETL script
- Create `database/migrations/migrate_question_database.py`
- Read CSV file
- Generate UUIDs for `question_id`
- Normalize opportunity types and subtypes
- Map questions to input types (text, textarea, number, radio)
- Add validation rules based on input type
- Add timestamps

**1.3.3** Add data validation to ETL
- Validate required fields (question_text, category)
- Check for duplicate questions
- Validate weight values (numeric or "Info")
- Normalize category names
- Handle missing data gracefully

**1.3.4** Run Question Database migration
- Execute ETL script
- Load all 1,042 questions into `form_builder.question_database`
- Verify record count matches CSV
- Spot-check 20 random questions for accuracy

**1.3.5** Create Question Database queries
- Write query to find questions by opportunity type
- Write query to filter by category
- Write query to search by keyword
- Save queries in `database/queries/question_queries.sql`

**1.3.6** Create CSV backup process
- Create `database/backups/` directory
- Copy original CSV with timestamp
- Create export script for BigQuery → CSV
- Document backup procedures

---

#### Task Group 1.4: Backend Project Setup (Day 2, 4 hours)

**1.4.1** Create backend directory structure
- Create `Q4 form scoring project/backend/` directory
- Create `backend/auth/` directory
- Create `backend/form_builder/` directory
- Create `backend/response_scorer/` directory
- Create `backend/common/` directory (shared utilities)
- Create `backend/tests/` directory

**1.4.2** Set up Python environment
- Create `backend/requirements.txt`
- Add dependencies:
  ```
  functions-framework>=3.0.0
  google-cloud-bigquery>=3.0.0
  google-cloud-storage>=2.0.0
  pyjwt>=2.8.0
  bcrypt>=4.0.0
  python-dotenv>=1.0.0
  requests>=2.31.0
  pytest>=7.4.0
  ```
- Create virtual environment: `python -m venv venv`
- Install dependencies: `pip install -r requirements.txt`

**1.4.3** Create shared utilities module
- Create `backend/common/bigquery_client.py`
  - BigQuery client initialization
  - Connection pooling
  - Error handling wrapper
- Create `backend/common/validators.py`
  - Email validation
  - Password strength validation
  - Input sanitization functions
- Create `backend/common/response_helpers.py`
  - Standard JSON response formatter
  - Error response builder
  - CORS headers helper

**1.4.4** Create configuration management
- Create `backend/common/config.py`
  - Load environment variables
  - BigQuery project/dataset names
  - JWT secret key
  - Token expiration times
  - API rate limits
- Create `.env.example` template
- Create `.gitignore` (exclude `.env`, `venv/`, etc.)

**1.4.5** Set up logging infrastructure
- Create `backend/common/logger.py`
  - Structured logging with Cloud Logging
  - Log levels configuration
  - Request ID tracking
  - Error alerting hooks
- Configure log retention policies

**1.4.6** Create testing framework
- Create `backend/tests/conftest.py` (pytest fixtures)
- Create mock BigQuery client
- Create test data generators
- Set up CI/CD test environment

---

### Week 2: Authentication System Development

#### Task Group 1.5: JWT Authentication API (Days 3-4, 12 hours)

**1.5.1** Design authentication API endpoints
- Document API contract:
  - `POST /auth/register` - Create new user
  - `POST /auth/login` - Authenticate and issue token
  - `POST /auth/logout` - Invalidate session
  - `POST /auth/refresh` - Refresh expired token
  - `GET /auth/me` - Get current user info
  - `POST /auth/reset-password` - Request password reset
  - `POST /auth/change-password` - Change password with token
- Write API specs in `backend/auth/API_SPEC.md`

**1.5.2** Implement password hashing utilities
- Create `backend/auth/password_utils.py`
- Implement `hash_password(password)` using bcrypt (12 rounds)
- Implement `verify_password(password, hash)`
- Add password strength checker (min 8 chars, upper, lower, number, special)
- Add tests for hashing functions

**1.5.3** Implement JWT token generation
- Create `backend/auth/jwt_utils.py`
- Implement `generate_token(user_id, email, permissions)`
  - Payload: `sub` (user_id), `email`, `permissions`, `iat`, `exp`
  - Use HS256 algorithm
  - Set expiration to 24 hours
- Implement `decode_token(token)`
  - Verify signature
  - Check expiration
  - Return payload or raise exception
- Implement `refresh_token(old_token)`
  - Validate old token (allow expired)
  - Issue new token with extended expiration
- Add tests for all token functions

**1.5.4** Implement user registration endpoint
- Create `backend/auth/main.py` (Cloud Function entry point)
- Implement `register_user(request)` function
  - Parse JSON body: `email`, `password`, `full_name`
  - Validate email format
  - Check password strength
  - Check if email already exists in `auth.users`
  - Hash password
  - Generate UUID for `user_id`
  - Insert into `auth.users` table
  - Return success/error response
- Add input validation and error handling
- Add rate limiting (max 5 registrations per IP per hour)

**1.5.5** Implement login endpoint
- Implement `login_user(request)` function in `backend/auth/main.py`
  - Parse JSON body: `email`, `password`
  - Query `auth.users` for matching email
  - Verify password with bcrypt
  - Query `auth.permission_groups` for user permissions
  - Generate JWT token with user info and permissions
  - Insert session record into `auth.sessions`
  - Update `last_login` timestamp in `auth.users`
  - Return token and user info
- Add brute force protection (lock account after 5 failed attempts)
- Log all login attempts (success and failure)

**1.5.6** Implement logout endpoint
- Implement `logout_user(request)` function
  - Extract JWT from Authorization header
  - Decode token to get `session_id`
  - Update `auth.sessions` set `is_active = false`
  - Add token to blacklist (for remaining validity period)
  - Return success response
- Handle edge case: already logged out

**1.5.7** Implement token refresh endpoint
- Implement `refresh_token_endpoint(request)` function
  - Extract expired JWT from Authorization header
  - Decode token (ignore expiration)
  - Verify session is still active in `auth.sessions`
  - Generate new token with same permissions
  - Update session record with new token hash
  - Return new token
- Validate refresh window (only allow within 7 days of expiration)

**1.5.8** Implement current user info endpoint
- Implement `get_current_user(request)` function
  - Extract JWT from Authorization header
  - Decode token
  - Query `auth.users` for user details
  - Query `auth.permission_groups` for permissions
  - Return user object with permissions
- Add caching layer (cache user info for 5 minutes)

**1.5.9** Implement password reset flow
- Implement `request_password_reset(request)` function
  - Parse JSON body: `email`
  - Check if user exists
  - Generate reset token (24-hour expiration)
  - Store token in `auth.password_reset_tokens` table (new table)
  - Send reset email (integrate with SendGrid or similar)
  - Return success (don't reveal if email exists)
- Implement `reset_password(request)` function
  - Parse JSON body: `reset_token`, `new_password`
  - Validate token from database
  - Check token not expired
  - Hash new password
  - Update `auth.users` password
  - Invalidate reset token
  - Invalidate all existing sessions for user
  - Return success

**1.5.10** Create authentication middleware
- Create `backend/common/auth_middleware.py`
- Implement `require_auth(handler)` decorator
  - Extract JWT from request header
  - Decode and validate token
  - Check session is active
  - Inject user info into request context
  - Call wrapped handler
  - Return 401 if validation fails
- Implement `require_permission(permission_level)` decorator
  - Check user has required permission level
  - Return 403 if insufficient permissions

**1.5.11** Deploy authentication Cloud Function
- Create `backend/auth/deploy.sh` script
- Deploy to Cloud Functions:
  ```bash
  gcloud functions deploy auth-api \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point auth_handler \
    --set-env-vars JWT_SECRET=$JWT_SECRET
  ```
- Test deployment with curl
- Document endpoint URL

**1.5.12** Write authentication API tests
- Create `backend/tests/test_auth.py`
- Test user registration (success, duplicate email, weak password)
- Test login (success, wrong password, locked account)
- Test logout (success, already logged out)
- Test token refresh (success, expired token, invalid token)
- Test current user endpoint (success, invalid token)
- Test password reset (success, invalid token, expired token)
- Run full test suite: `pytest backend/tests/`

---

#### Task Group 1.6: Login UI Development (Days 4-5, 12 hours)

**1.6.1** Set up React project for authentication UI
- Create `Q4 form scoring project/frontend/` directory
- Initialize React app: `npm create vite@latest auth-ui -- --template react`
- Navigate to `frontend/auth-ui/`
- Install dependencies:
  ```bash
  npm install axios react-router-dom jwt-decode
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```
- Configure Tailwind CSS in `tailwind.config.js`

**1.6.2** Create authentication context and state management
- Create `frontend/auth-ui/src/context/AuthContext.jsx`
- Implement AuthProvider component
  - State: `user`, `token`, `isAuthenticated`, `isLoading`
  - Functions: `login()`, `logout()`, `register()`, `refreshToken()`
  - Store token in localStorage
  - Auto-refresh token before expiration
- Implement useAuth() custom hook

**1.6.3** Create API client for authentication
- Create `frontend/auth-ui/src/services/authApi.js`
- Implement axios instance with base URL
- Implement API methods:
  - `register(email, password, fullName)`
  - `login(email, password)`
  - `logout()`
  - `refreshToken()`
  - `getCurrentUser()`
  - `requestPasswordReset(email)`
  - `resetPassword(token, newPassword)`
- Add request interceptor (attach JWT to headers)
- Add response interceptor (handle 401, refresh token)

**1.6.4** Design and implement Login page
- Create `frontend/auth-ui/src/pages/Login.jsx`
- Form fields: Email, Password
- "Remember me" checkbox
- "Forgot password?" link
- Submit button
- Link to registration page
- Apply Opex branding (navy #1a2859, cyan #00c4cc)
- Add form validation (client-side)
- Show loading spinner during API call
- Display error messages
- Redirect to dashboard on success

**1.6.5** Design and implement Registration page
- Create `frontend/auth-ui/src/pages/Register.jsx`
- Form fields: Full Name, Email, Password, Confirm Password
- Password strength indicator
- Terms of service checkbox
- Submit button
- Link to login page
- Apply Opex branding
- Add form validation:
  - Email format
  - Password strength (8+ chars, upper, lower, number, special)
  - Passwords match
- Display error messages
- Show success message and redirect to login

**1.6.6** Design and implement Forgot Password page
- Create `frontend/auth-ui/src/pages/ForgotPassword.jsx`
- Form field: Email
- Submit button
- Back to login link
- Show success message (email sent)
- Handle errors

**1.6.7** Design and implement Reset Password page
- Create `frontend/auth-ui/src/pages/ResetPassword.jsx`
- Parse reset token from URL query parameter
- Form fields: New Password, Confirm Password
- Password strength indicator
- Submit button
- Show success message and redirect to login
- Handle expired/invalid token errors

**1.6.8** Create protected route component
- Create `frontend/auth-ui/src/components/ProtectedRoute.jsx`
- Check if user is authenticated
- Redirect to login if not authenticated
- Show loading spinner while checking auth
- Allow route if authenticated

**1.6.9** Implement navigation and routing
- Create `frontend/auth-ui/src/App.jsx`
- Set up React Router:
  - `/login` - Login page
  - `/register` - Registration page
  - `/forgot-password` - Forgot password page
  - `/reset-password` - Reset password page
  - `/` - Redirect to login if not authenticated, dashboard if authenticated
- Wrap app in AuthProvider

**1.6.10** Create reusable form components
- Create `frontend/auth-ui/src/components/Input.jsx` (styled input)
- Create `frontend/auth-ui/src/components/Button.jsx` (styled button)
- Create `frontend/auth-ui/src/components/Alert.jsx` (error/success messages)
- Create `frontend/auth-ui/src/components/PasswordStrengthIndicator.jsx`
- Apply consistent styling with Tailwind

**1.6.11** Add loading states and error handling
- Create `frontend/auth-ui/src/components/LoadingSpinner.jsx`
- Add loading state to all forms during API calls
- Display user-friendly error messages
- Handle network errors gracefully
- Add timeout handling (30 seconds)

**1.6.12** Test authentication UI
- Manual testing:
  - Test registration flow (success, errors)
  - Test login flow (success, errors)
  - Test logout
  - Test password reset flow
  - Test token refresh
  - Test protected routes
- Browser testing (Chrome, Firefox, Safari)
- Mobile responsive testing
- Fix any UI bugs

---

#### Task Group 1.7: API Gateway Setup (Day 5, 6 hours)

**1.7.1** Design API Gateway architecture
- Document routing rules:
  - `/auth/*` → auth-api Cloud Function
  - `/form-builder/*` → form-builder-api Cloud Function
  - `/response-scorer/*` → response-scorer-api Cloud Function
  - `/webhook/*` → existing webhook (backward compatibility)
- Document authentication requirements per route
- Document rate limiting rules

**1.7.2** Create API Gateway configuration
- Create `backend/api-gateway/gateway-config.yaml`
- Define OpenAPI 3.0 specification
- Define all endpoints with request/response schemas
- Define security schemes (JWT)
- Define rate limiting (100 requests/minute per user)

**1.7.3** Deploy API Gateway
- Use Google Cloud API Gateway
- Deploy configuration:
  ```bash
  gcloud api-gateway api-configs create opex-gateway-config \
    --api=opex-api \
    --openapi-spec=gateway-config.yaml \
    --backend-auth-service-account=opex-api@opex-data-lake-k23k4y98m.iam.gserviceaccount.com
  ```
- Get gateway URL
- Test all routes with curl

**1.7.4** Implement rate limiting
- Create `backend/common/rate_limiter.py`
- Use Redis or Cloud Memorystore for rate limit tracking
- Implement sliding window rate limiter
- Return 429 (Too Many Requests) when limit exceeded
- Add rate limit headers to responses

**1.7.5** Add API Gateway monitoring
- Enable Cloud Monitoring for API Gateway
- Create dashboard for API metrics:
  - Request count by endpoint
  - Response times (p50, p95, p99)
  - Error rates (4xx, 5xx)
  - Rate limit hits
- Set up alerting:
  - Alert if error rate > 5%
  - Alert if p95 latency > 2 seconds
  - Alert if rate limit hits spike

**1.7.6** Document API Gateway
- Create `backend/api-gateway/README.md`
- Document all endpoints with examples
- Document authentication process
- Document rate limits
- Provide curl examples for all operations

---

#### Task Group 1.8: Permission Management (Day 5, 6 hours)

**1.8.1** Create permission management API
- Create `backend/auth/permissions.py`
- Implement `grant_permission(user_id, company, category, level, granted_by)`
  - Validate permission level (view, edit, admin)
  - Check granting user has admin permission
  - Insert into `auth.permission_groups`
  - Log action in `scoring.audit_trail`
  - Return success
- Implement `revoke_permission(permission_id, revoked_by)`
  - Validate permission exists
  - Check revoking user has admin permission
  - Delete from `auth.permission_groups`
  - Log action in `scoring.audit_trail`
- Implement `get_user_permissions(user_id)`
  - Query all permissions for user
  - Return structured list
- Implement `list_all_permissions(filter_by_company, filter_by_category)`
  - Admin-only endpoint
  - Return paginated list of all permissions

**1.8.2** Implement permission checking utilities
- Create `backend/common/permissions.py`
- Implement `check_permission(user_id, company, category, required_level)`
  - Query user's permission level for company/category
  - Return True if user has required level or higher
  - Admin > Edit > View hierarchy
- Implement `get_accessible_companies(user_id)`
  - Return list of companies user can access
- Implement `get_accessible_categories(user_id, company)`
  - Return list of categories user can access for a company

**1.8.3** Create permission management UI components
- Create `frontend/auth-ui/src/pages/PermissionManagement.jsx` (admin only)
- Display table of all users and their permissions
- Add "Grant Permission" button
- Add "Revoke Permission" button
- Add filters: company, category, permission level
- Add search by user email

**1.8.4** Create permission grant modal
- Create `frontend/auth-ui/src/components/GrantPermissionModal.jsx`
- Form fields:
  - User (search by email)
  - Company (dropdown or text input)
  - Category (dropdown)
  - Permission Level (dropdown: view, edit, admin)
- Submit button
- Handle API call
- Show success/error messages

**1.8.5** Seed initial admin user
- Create `database/seed_data/create_admin_user.py`
- Create admin user account:
  - Email: `admin@opextechnologies.com`
  - Password: (generate secure password, output to console)
  - Full name: "System Administrator"
- Grant admin permissions for all companies and categories
- Document admin credentials securely

**1.8.6** Test permission system end-to-end
- Create test users with different permission levels
- Test view permission (can read, cannot write)
- Test edit permission (can read and write)
- Test admin permission (can manage permissions)
- Test permission inheritance
- Test permission revocation

---

#### Phase 1 Deliverables Checklist

- [ ] BigQuery schema deployed (11 new tables)
- [ ] Question Database migrated (1,042 questions)
- [ ] Authentication API deployed and tested
- [ ] Login UI deployed and functional
- [ ] JWT token generation and validation working
- [ ] Permission system implemented
- [ ] API Gateway configured and deployed
- [ ] Rate limiting active
- [ ] Monitoring dashboards created
- [ ] Admin user created
- [ ] Documentation complete
- [ ] All tests passing

---

## Phase 2: Form Builder Development (Weeks 3-4)

**Objective:** Build web application for creating and deploying survey forms

**Hours:** 96 hours
**Cost:** $7,200
**Dependencies:** Phase 1 (Authentication) must be complete

---

### Week 3: Form Builder Backend & Question Management

#### Task Group 2.1: Form Builder API - CRUD Operations (Days 1-2, 12 hours)

**2.1.1** Design Form Builder API endpoints
- Document API contract:
  - `GET /form-builder/templates` - List all form templates
  - `GET /form-builder/templates/:id` - Get specific template
  - `POST /form-builder/templates` - Create new template
  - `PUT /form-builder/templates/:id` - Update template
  - `DELETE /form-builder/templates/:id` - Delete template
  - `POST /form-builder/templates/:id/deploy` - Deploy to GitHub
  - `GET /form-builder/questions` - Query question database
  - `POST /form-builder/preview` - Generate preview HTML
- Write API specs in `backend/form_builder/API_SPEC.md`

**2.1.2** Implement form template creation endpoint
- Create `backend/form_builder/main.py`
- Implement `create_template(request)` function
  - Parse JSON body: `template_name`, `opportunity_type`, `opportunity_subtype`, `questions` (array)
  - Validate authentication (require edit permission)
  - Validate inputs:
    - Template name is unique
    - Opportunity type/subtype are valid
    - Questions array is not empty
    - Each question has: `question_id`, `weight`, `is_required`, `input_type`
  - Generate UUID for `template_id`
  - Insert into `form_builder.form_templates` with status "draft"
  - Log action in `scoring.audit_trail`
  - Return template object with ID
- Add tests

**2.1.3** Implement form template retrieval endpoints
- Implement `list_templates(request)` function
  - Support filtering by: `opportunity_type`, `opportunity_subtype`, `status`, `created_by`
  - Support pagination: `limit`, `offset`
  - Support sorting: `created_at` DESC by default
  - Return paginated list of templates
  - Filter by user permissions (only show templates for accessible categories)
- Implement `get_template(request, template_id)` function
  - Validate template exists
  - Check user has view permission
  - Return full template object with questions array
  - Include metadata: created_by (user email), created_at, updated_at, deployed_url

**2.1.4** Implement form template update endpoint
- Implement `update_template(request, template_id)` function
  - Validate authentication (require edit permission)
  - Parse JSON body (partial update supported)
  - Validate template exists
  - Check template status is "draft" (cannot edit published templates)
  - Update fields in `form_builder.form_templates`
  - Increment `version` number
  - Update `updated_at` timestamp
  - Log action in `scoring.audit_trail`
  - Return updated template object

**2.1.5** Implement form template deletion endpoint
- Implement `delete_template(request, template_id)` function
  - Validate authentication (require admin permission)
  - Validate template exists
  - Check template status (only allow delete if "draft" or "archived")
  - Soft delete: update status to "deleted"
  - Log action in `scoring.audit_trail`
  - Return success message

**2.1.6** Implement question query endpoint
- Implement `query_questions(request)` function
  - Support filtering by:
    - `category` (Overview, Help Desk, etc.)
    - `opportunity_type` (All, Managed Service Provider, etc.)
    - `opportunity_subtype` (All, SASE, SD-WAN, etc.)
    - `search` (keyword search in question_text)
  - Support pagination
  - Query `form_builder.question_database`
  - Return list of questions with all metadata
  - Include `is_selected` flag if template_id provided (show which questions are already in template)

**2.1.7** Implement question detail endpoint
- Implement `get_question(request, question_id)` function
  - Validate question exists
  - Return full question object
  - Include usage statistics (how many templates use this question)

**2.1.8** Add question management endpoints (admin only)
- Implement `create_question(request)` (admin only)
  - Parse JSON body with all question fields
  - Validate inputs
  - Generate UUID for `question_id`
  - Insert into `form_builder.question_database`
  - Return question object
- Implement `update_question(request, question_id)` (admin only)
  - Update question fields
  - Increment version number
  - Log changes in audit trail
- Implement `delete_question(request, question_id)` (admin only)
  - Soft delete: set `is_active = false`
  - Check if question is used in any templates
  - Warn if question is in use

**2.1.9** Deploy Form Builder API to Cloud Functions
- Create `backend/form_builder/deploy.sh`
- Deploy:
  ```bash
  gcloud functions deploy form-builder-api \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point form_builder_handler \
    --set-env-vars JWT_SECRET=$JWT_SECRET
  ```
- Update API Gateway configuration to route to new function
- Test all endpoints with curl

**2.1.10** Write Form Builder API tests
- Create `backend/tests/test_form_builder_api.py`
- Test template CRUD operations
- Test question query with various filters
- Test permission enforcement
- Test error cases (invalid input, unauthorized access)
- Run test suite

---

#### Task Group 2.2: Form Generation Logic (Days 2-3, 12 hours)

**2.2.1** Analyze existing form structure
- Read one of the existing forms: `Web/surveys/security-sase-survey.html`
- Document HTML structure:
  - Header section (logo, title)
  - Form container
  - Question rendering logic (JavaScript)
  - Input type handling (text, textarea, number, radio)
  - Progress bar
  - Submit button and handler
  - Webhook integration
- Extract reusable template patterns

**2.2.2** Create form HTML template
- Create `backend/form_builder/templates/form_template.html`
- Design template with placeholders:
  - `{{FORM_TITLE}}` - Survey name
  - `{{SURVEY_TYPE}}` - Survey type identifier
  - `{{QUESTIONS_JSON}}` - JavaScript array of questions
  - `{{WEBHOOK_URL}}` - Cloud Function webhook URL
  - `{{OPEX_LOGO_URL}}` - Logo URL
  - `{{PRIMARY_COLOR}}` - Branding color
- Use Jinja2 template syntax
- Include all CSS styling inline
- Include all JavaScript inline (no external dependencies)
- Maintain responsive design

**2.2.3** Create form generation service
- Create `backend/form_builder/form_generator.py`
- Implement `generate_form_html(template)` function
  - Accept template object (from database)
  - Query questions from `form_builder.question_database`
  - Build questions array with:
    - Question text
    - Input type
    - Field ID (sanitized)
    - Required flag
    - Help text
  - Render HTML template with Jinja2
  - Return complete HTML string
- Add error handling

**2.2.4** Implement question rendering logic
- Create `backend/form_builder/question_renderer.py`
- Implement `render_question(question, field_id)` function
  - Handle input types:
    - `text` - Single line text input
    - `textarea` - Multi-line text input
    - `number` - Numeric input with validation
    - `radio` - Yes/No/Partial radio buttons
    - `select` - Dropdown (if options provided)
    - `checkbox` - Multiple selection (if options provided)
  - Generate HTML for each type
  - Add required attribute if needed
  - Add help text tooltip if present
  - Apply consistent styling

**2.2.5** Implement form validation rules
- Create `backend/form_builder/form_validator.py`
- Implement client-side validation JavaScript:
  - Required field validation
  - Email format validation
  - Phone number format validation
  - Numeric range validation
  - URL format validation
  - Custom regex validation (if specified in question)
- Embed validation code in generated form
- Show validation errors inline

**2.2.6** Implement progress tracking
- Add progress bar JavaScript to template
- Calculate progress as: (answered questions / total required questions) * 100
- Update progress bar as user fills form
- Change color as progress increases (red → yellow → green)

**2.2.7** Implement form submission handler
- Add submission JavaScript to template:
  - Prevent default form submission
  - Collect all form data into JSON object
  - Sanitize field names (spaces → underscores, lowercase)
  - Add metadata:
    - `timestamp` (ISO format)
    - `source` (form identifier)
  - Show loading spinner
  - POST to webhook URL
  - Handle success response (show thank you message)
  - Handle error response (show error, allow retry)
  - Disable double submission

**2.2.8** Create form preview endpoint
- Implement `preview_form(request)` in `backend/form_builder/main.py`
  - Parse JSON body with template data (may not be saved yet)
  - Generate form HTML
  - Return HTML string
  - Set `Content-Type: text/html`
- This allows live preview in Form Builder UI

**2.2.9** Test form generation
- Create test template with various question types
- Generate HTML
- Save HTML to file
- Open in browser and test:
  - All questions render correctly
  - Validation works
  - Progress bar updates
  - Submission works (use test webhook)
- Test on mobile devices

**2.2.10** Optimize generated HTML
- Minify CSS and JavaScript
- Compress HTML (remove whitespace)
- Inline critical CSS
- Lazy load images
- Target file size < 200KB per form

---

#### Task Group 2.3: GitHub API Integration (Days 3-4, 12 hours)

**2.3.1** Set up GitHub authentication
- Create GitHub personal access token with repo permissions
- Store token in Cloud Secret Manager:
  ```bash
  echo -n "ghp_xxxxx" | gcloud secrets create github-token --data-file=-
  ```
- Grant Cloud Function access to secret
- Document token management procedures

**2.3.2** Create GitHub client utility
- Create `backend/form_builder/github_client.py`
- Implement `GitHubClient` class
  - Initialize with token from Secret Manager
  - Use PyGithub library or requests
  - Methods:
    - `get_repo(owner, repo_name)` - Get repository object
    - `create_file(repo, path, content, message)` - Create new file
    - `update_file(repo, path, content, message)` - Update existing file
    - `get_file_content(repo, path)` - Read file content
    - `delete_file(repo, path, message)` - Delete file
    - `create_branch(repo, branch_name, from_branch)` - Create branch
- Add error handling for GitHub API errors (rate limits, authentication, etc.)

**2.3.3** Design deployment workflow
- Document deployment process:
  1. Generate form HTML from template
  2. Create/update file in GitHub repo
  3. File path: `forms/{opportunity_type}/{template_name}.html`
  4. Commit message: "Deploy {template_name} form (version {version})"
  5. GitHub Pages automatically publishes to: `https://yourusername.github.io/repo-name/forms/...`
  6. Update template record with deployed_url
- Consider branch strategy (deploy to main or separate branch)

**2.3.4** Implement form deployment endpoint
- Implement `deploy_form(request, template_id)` in `backend/form_builder/main.py`
  - Validate authentication (require edit permission)
  - Validate template exists
  - Retrieve template from database
  - Generate form HTML using `form_generator.generate_form_html()`
  - Determine GitHub file path
  - Check if file already exists (create vs update)
  - Use `GitHubClient` to create/update file
  - Commit with descriptive message
  - Calculate deployed URL (based on GitHub Pages configuration)
  - Update template record:
    - Set `status = "published"`
    - Set `deployed_url`
    - Set `github_repo_path`
    - Update `updated_at`
  - Log deployment in `scoring.audit_trail`
  - Return deployed URL

**2.3.5** Implement deployment rollback
- Implement `rollback_deployment(request, template_id, version)` function
  - Validate template exists
  - Check user has admin permission
  - Retrieve template at specified version (need version history table)
  - Generate HTML for that version
  - Deploy to GitHub (overwrite current)
  - Update template record
  - Log rollback action

**2.3.6** Add deployment status tracking
- Create `form_builder.deployment_history` table:
  - Columns: `deployment_id`, `template_id`, `version`, `deployed_by`, `deployed_at`, `github_commit_sha`, `deployed_url`, `status` (success/failed), `error_message`
- Insert record for each deployment attempt
- Query deployment history for a template

**2.3.7** Implement webhook auto-configuration
- Design webhook configuration:
  - Each form POSTs to same webhook URL (existing Cloud Function)
  - Form includes `formName` in payload to distinguish forms
  - Webhook automatically creates BigQuery table based on formName
- Add webhook URL to generated form HTML
- No additional configuration needed (already working!)

**2.3.8** Create deployment notification system
- Implement email/Slack notifications for deployments
- Notify when deployment succeeds
- Notify when deployment fails (with error details)
- Include deployed URL in notification
- Optional: Create Slack webhook integration

**2.3.9** Test GitHub integration
- Create test GitHub repository (or use existing)
- Enable GitHub Pages
- Test file creation (deploy new form)
- Verify file appears in repo
- Test file update (re-deploy form)
- Verify GitHub Pages updates (may take 1-2 minutes)
- Test deployed form URL in browser
- Test form submission works

**2.3.10** Handle GitHub API rate limits
- GitHub API has rate limits (5,000 requests/hour for authenticated)
- Implement rate limit checking:
  - Check remaining rate limit before each API call
  - If limit low, delay requests or reject with 429
  - Cache GitHub API responses when possible
- Add retry logic with exponential backoff for rate limit errors

**2.3.11** Add deployment preview
- Implement `get_deployment_preview(template_id)` endpoint
  - Generate form HTML
  - Return preview URL (temporary URL for testing)
  - Option 1: Upload to Cloud Storage bucket (public, temporary)
  - Option 2: Return HTML directly (user saves to file)
- Allow testing before committing to GitHub

**2.3.12** Document GitHub integration
- Create `backend/form_builder/GITHUB_SETUP.md`
- Document:
  - GitHub token creation steps
  - Repository setup (enable GitHub Pages)
  - Branch configuration
  - Custom domain setup (optional)
  - Troubleshooting common issues

---

### Week 4: Form Builder Frontend

#### Task Group 2.4: Form Builder UI Foundation (Days 1-2, 12 hours)

**2.4.1** Set up Form Builder React project
- Create `frontend/form-builder/` directory
- Initialize React app: `npm create vite@latest form-builder -- --template react`
- Install dependencies:
  ```bash
  npm install axios react-router-dom
  npm install @tanstack/react-query
  npm install react-hook-form
  npm install react-hot-toast
  npm install lucide-react
  npm install -D tailwindcss
  ```
- Configure Tailwind CSS
- Set up project structure:
  - `src/pages/` - Page components
  - `src/components/` - Reusable components
  - `src/services/` - API clients
  - `src/hooks/` - Custom hooks
  - `src/utils/` - Utility functions

**2.4.2** Create API client for Form Builder
- Create `frontend/form-builder/src/services/formBuilderApi.js`
- Implement axios instance with auth headers
- Implement API methods:
  - `fetchTemplates(filters, pagination)`
  - `fetchTemplate(templateId)`
  - `createTemplate(templateData)`
  - `updateTemplate(templateId, updates)`
  - `deleteTemplate(templateId)`
  - `deployTemplate(templateId)`
  - `fetchQuestions(filters)`
  - `previewForm(templateData)`
- Add error handling and retry logic

**2.4.3** Create shared layout and navigation
- Create `frontend/form-builder/src/components/Layout.jsx`
- Header with:
  - Opex logo
  - App title: "Form Builder"
  - User menu (profile, logout)
  - Navigation links
- Sidebar navigation:
  - Dashboard
  - Form Templates
  - Question Database
  - Deployment History
- Apply Opex branding

**2.4.4** Create dashboard page
- Create `frontend/form-builder/src/pages/Dashboard.jsx`
- Show key metrics:
  - Total templates created
  - Total templates deployed
  - Recent activity (last 10 actions)
  - Quick actions (Create New Form button)
- Display stats using cards

**2.4.5** Create template list page
- Create `frontend/form-builder/src/pages/TemplateList.jsx`
- Display table of all templates:
  - Columns: Name, Type, Status, Created By, Created At, Actions
  - Actions: View, Edit, Deploy, Delete
- Add filtering:
  - By opportunity type
  - By status (draft, published, archived)
  - By created_by
- Add search bar (search by name)
- Add pagination
- Add "Create New Template" button

**2.4.6** Create template card component
- Create `frontend/form-builder/src/components/TemplateCard.jsx`
- Display template summary:
  - Template name
  - Opportunity type/subtype
  - Number of questions
  - Status badge (color-coded)
  - Last updated timestamp
  - Deployed URL (if published)
- Add action buttons (Edit, Deploy, Delete)
- Add hover effects

**2.4.7** Implement template deletion
- Add confirmation modal for deletion
- Call API to delete template
- Show success/error toast notification
- Refresh template list

**2.4.8** Add loading states and error handling
- Create `frontend/form-builder/src/components/LoadingSpinner.jsx`
- Create `frontend/form-builder/src/components/ErrorMessage.jsx`
- Show loading spinner while fetching data
- Display user-friendly error messages
- Add retry button for failed requests

---

#### Task Group 2.5: Form Builder Core Features (Days 2-3, 16 hours)

**2.5.1** Create template editor page layout
- Create `frontend/form-builder/src/pages/TemplateEditor.jsx`
- Three-column layout:
  - Left sidebar: Question database browser
  - Center: Selected questions list (form builder)
  - Right sidebar: Form preview
- Make responsive (collapse sidebars on mobile)

**2.5.2** Implement question database browser
- Create `frontend/form-builder/src/components/QuestionBrowser.jsx`
- Display filterable list of questions:
  - Filter by category (dropdown)
  - Filter by opportunity type (dropdown)
  - Search by keyword (text input)
- Display questions as cards:
  - Question text
  - Category badge
  - Default weight
  - Add button (+)
- Implement pagination (load more)
- Highlight questions already added to form

**2.5.3** Implement drag-and-drop question selection
- Install `@dnd-kit/core` for drag and drop:
  ```bash
  npm install @dnd-kit/core @dnd-kit/sortable
  ```
- Make question cards draggable
- Make center column a drop zone
- Allow dragging questions from browser to form
- Allow reordering questions within form
- Add visual feedback (drag preview, drop target highlighting)

**2.5.4** Create selected questions list
- Create `frontend/form-builder/src/components/SelectedQuestionsList.jsx`
- Display questions added to form:
  - Question text
  - Category
  - Weight (editable)
  - Required toggle
  - Input type dropdown
  - Remove button (X)
  - Reorder handles (drag)
- Make list scrollable
- Show empty state if no questions selected

**2.5.5** Implement question customization
- For each selected question, allow editing:
  - Weight (number input, default from database)
  - Required (checkbox toggle)
  - Input type (dropdown: text, textarea, number, radio, select)
  - Help text (optional text input)
  - Validation rules (advanced)
- Show edit modal/panel when clicking on question
- Save changes immediately (local state)

**2.5.6** Create form metadata editor
- Create `frontend/form-builder/src/components/FormMetadata.jsx`
- Form fields at top of editor:
  - Template name (text input, required)
  - Opportunity type (dropdown, required)
  - Opportunity subtype (dropdown, required)
  - Description (textarea, optional)
- Validate required fields
- Show character count for text inputs

**2.5.7** Implement real-time form preview
- Create `frontend/form-builder/src/components/FormPreview.jsx`
- Display iframe or live preview of generated form
- Preview updates as questions are added/removed/reordered
- Preview shows actual form styling (Opex branding)
- Call `previewForm()` API endpoint on changes (debounced)
- Show loading state while generating preview

**2.5.8** Implement save draft functionality
- Add "Save as Draft" button in header
- Validate form metadata (name, type required)
- Collect all form data (metadata + questions array)
- Call `createTemplate()` or `updateTemplate()` API
- Show success toast: "Draft saved"
- Update URL to include template_id (for editing existing)
- Handle errors (show error toast)

**2.5.9** Implement template loading for editing
- On page load, check if `template_id` in URL
- If present, fetch template from API
- Populate form metadata fields
- Populate selected questions list
- Set page title: "Edit Template: {name}"
- Allow editing and saving updates

**2.5.10** Add question search within builder
- Add search bar above selected questions list
- Filter displayed questions by search term
- Highlight matching text
- Don't modify actual form data, just filter display

**2.5.11** Add bulk actions
- Add "Select All" checkbox
- Allow selecting multiple questions
- Bulk actions:
  - Remove selected questions
  - Set weight for selected questions
  - Mark selected as required/optional
- Add confirmation for bulk delete

**2.5.12** Implement undo/redo functionality
- Track change history (add question, remove question, reorder, edit weight)
- Add Undo button (Ctrl+Z)
- Add Redo button (Ctrl+Y)
- Limit history to last 20 actions
- Persist history in memory (don't save to database)

---

#### Task Group 2.6: Form Deployment UI (Day 4, 8 hours)

**2.6.1** Create deployment configuration modal
- Create `frontend/form-builder/src/components/DeploymentModal.jsx`
- Show before deploying:
  - Template name
  - Number of questions
  - Last deployed date (if previously deployed)
  - Target URL preview
  - Deployment options:
    - Overwrite existing form (if applicable)
    - Deploy to production (vs staging)
- Add "Deploy" and "Cancel" buttons

**2.6.2** Implement deployment flow
- Add "Deploy Form" button in template editor header
- Validate form before deploying:
  - Template must be saved (not just local changes)
  - Template name is valid
  - At least one question selected
- Open deployment modal
- On confirm, call `deployTemplate(templateId)` API
- Show progress indicator (deploying...)
- On success:
  - Show success message with deployed URL
  - Update template status to "published"
  - Show "View Form" button (opens deployed URL)
- On error:
  - Show error message
  - Allow retry

**2.6.3** Create deployment history page
- Create `frontend/form-builder/src/pages/DeploymentHistory.jsx`
- Display table of all deployments:
  - Columns: Template Name, Version, Deployed By, Deployed At, Status, URL
  - Color-code status (success = green, failed = red)
- Add filtering by template
- Add sorting by date (newest first)
- Add "View Form" link for successful deployments

**2.6.4** Implement deployment status polling
- After triggering deployment, poll API for status
- Show progress:
  - Generating form HTML... ✓
  - Uploading to GitHub... ✓
  - Waiting for GitHub Pages... ⏳
  - Deployed! ✓
- Handle timeout (if GitHub Pages takes too long)

**2.6.5** Add deployment preview
- Add "Preview" button next to "Deploy" button
- Generate preview URL (temporary)
- Open preview in new tab
- Allow testing before deploying to production

**2.6.6** Create deployed form management
- Add "View Deployed Forms" page
- List all published templates with their URLs
- Show QR code for each form (for easy mobile access)
- Add "Copy URL" button
- Add "Open in New Tab" button
- Show deployment stats (views, submissions - if tracked)

**2.6.7** Implement form URL customization (optional)
- Allow customizing the deployed URL path
- Default: `forms/{type}/{template-name}.html`
- Custom: User can specify custom slug
- Validate slug (alphanumeric, hyphens only)
- Check for conflicts (slug already used)

**2.6.8** Add post-deployment actions
- After successful deployment, show options:
  - Share form (copy URL, send email, create QR code)
  - Edit form (return to editor)
  - Create another form (go to new template page)
  - View responses (open Response Scorer)

---

#### Task Group 2.7: Testing and Polish (Day 4, 8 hours)

**2.7.1** Test complete form builder workflow
- Create new template from scratch
- Add questions from database
- Customize weights and input types
- Reorder questions
- Save draft
- Preview form
- Deploy form
- Verify deployed form works
- Test form submission
- Check data appears in BigQuery

**2.7.2** Test editing existing template
- Open existing template
- Modify questions
- Save changes
- Re-deploy
- Verify changes reflected in deployed form

**2.7.3** Test error scenarios
- Try to deploy without saving
- Try to save with missing required fields
- Test network errors (disconnect internet)
- Test API errors (invalid auth token)
- Test GitHub errors (invalid repo)
- Verify error messages are user-friendly

**2.7.4** Test responsive design
- Test on desktop (1920x1080)
- Test on tablet (768x1024)
- Test on mobile (375x667)
- Verify all features work on mobile
- Verify drag-and-drop works on touch devices

**2.7.5** Cross-browser testing
- Test in Chrome
- Test in Firefox
- Test in Safari
- Test in Edge
- Fix any browser-specific bugs

**2.7.6** Performance optimization
- Measure page load time (target < 2 seconds)
- Lazy load question database (load on scroll)
- Debounce form preview updates (500ms)
- Optimize images (compress logos)
- Minify JavaScript and CSS

**2.7.7** Accessibility improvements
- Add ARIA labels to all interactive elements
- Ensure keyboard navigation works (Tab, Enter, Escape)
- Test with screen reader
- Ensure color contrast meets WCAG AA standards
- Add focus indicators

**2.7.8** Add user guidance
- Add tooltips to explain features
- Add "?" help icons next to complex fields
- Create onboarding tour (optional, using react-joyride)
- Add empty states with helpful instructions
- Add placeholder text in inputs

---

#### Phase 2 Deliverables Checklist

- [ ] Form Builder API deployed (8+ endpoints)
- [ ] Question Database migrated to BigQuery
- [ ] Form generation logic implemented
- [ ] GitHub API integration working
- [ ] Form Builder UI complete
- [ ] Question browser functional
- [ ] Drag-and-drop question selection working
- [ ] Real-time form preview working
- [ ] Deployment to GitHub Pages working
- [ ] Template CRUD operations working
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Form Builder accessible at production URL

---

## Phase 3: Response Scorer Development (Weeks 5-6)

**Objective:** Build web application for viewing, filtering, and scoring survey responses

**Hours:** 64 hours
**Cost:** $4,800
**Dependencies:** Phase 1 (Authentication) complete

---

### Week 5: Response Scorer Backend

#### Task Group 3.1: Response Scorer API (Days 1-2, 12 hours)

**3.1.1** Design Response Scorer API endpoints
- Document API contract:
  - `GET /response-scorer/responses` - List all responses (with filters)
  - `GET /response-scorer/responses/:id` - Get specific response detail
  - `GET /response-scorer/surveys` - List available survey types
  - `GET /response-scorer/scores` - List scored responses
  - `GET /response-scorer/scores/:id` - Get specific score
  - `POST /response-scorer/scores` - Create new score
  - `PUT /response-scorer/scores/:id` - Update score
  - `DELETE /response-scorer/scores/:id` - Delete score
  - `POST /response-scorer/scores/:id/submit` - Submit score for approval
- Write API specs in `backend/response_scorer/API_SPEC.md`

**3.1.2** Implement response retrieval endpoint
- Create `backend/response_scorer/main.py`
- Implement `list_responses(request)` function
  - Query `scoring.all_survey_responses` view
  - Support filtering by:
    - `company_name` (text search)
    - `survey_type` (exact match)
    - `source` (web-form, backload, etc.)
    - `date_range` (start_date, end_date)
    - `scored_status` (unscored, in_progress, completed)
  - Support sorting by timestamp (DESC/ASC)
  - Support pagination (limit, offset)
  - Filter by user permissions (only show responses for accessible companies/categories)
  - Return paginated list with metadata:
    - Total count
    - Filtered count
    - Available filters (unique values for each filter field)

**3.1.3** Implement response detail endpoint
- Implement `get_response_detail(request, response_id)` function
  - Query specific response from `opex_dev` tables (wide format)
  - Include all metadata (contact info, timestamp, source)
  - Include all question-answer pairs
  - Include scoring status (check if score exists)
  - Include related scores (historical scores for this response)
  - Return full response object

**3.1.4** Implement surveys list endpoint
- Implement `list_surveys(request)` function
  - Query distinct survey types from `scoring.all_survey_responses`
  - Return list with counts:
    - Survey type name
    - Total responses
    - Unscored responses
    - Last response date
  - Filter by user permissions

**3.1.5** Implement score creation endpoint
- Implement `create_score(request)` function
  - Parse JSON body:
    - `response_id` (link to source response)
    - `company_name`
    - `survey_type`
    - `question_scores` (array of {question, answer, weight, points_awarded, comments})
    - `notes` (overall scoring notes)
  - Validate authentication (require edit permission)
  - Generate UUID for `score_id`
  - Calculate `total_score` (sum of points_awarded)
  - Calculate `max_score` (sum of max_points)
  - Calculate `percentage` (total_score / max_score * 100)
  - Insert into `scoring.scored_responses` with status "draft"
  - Insert question scores into `scoring.question_scores`
  - Log action in `scoring.audit_trail`
  - Return score object with ID

**3.1.6** Implement score update endpoint
- Implement `update_score(request, score_id)` function
  - Validate authentication (require edit permission)
  - Validate score exists
  - Check score status (can only edit if "draft" or "in_progress")
  - Parse JSON body (partial update)
  - Update `scoring.scored_responses`
  - Update `scoring.question_scores` if question scores changed
  - Recalculate total_score, max_score, percentage
  - Update `updated_at` timestamp
  - Log changes in `scoring.audit_trail` (track what changed)
  - Return updated score object

**3.1.7** Implement score retrieval endpoints
- Implement `list_scores(request)` function
  - Query `scoring.scored_responses`
  - Support filtering by company_name, survey_type, scored_by, status, date_range
  - Support sorting and pagination
  - Return list of scores with summary data
- Implement `get_score_detail(request, score_id)` function
  - Query full score from `scoring.scored_responses`
  - Join with `scoring.question_scores` to get all question scores
  - Return complete score object

**3.1.8** Implement score submission endpoint
- Implement `submit_score(request, score_id)` function
  - Validate authentication (require edit permission)
  - Validate score exists
  - Check score is "draft" or "in_progress"
  - Validate score is complete (all required questions scored)
  - Update status to "submitted"
  - Log submission in audit trail
  - Optional: Send notification to approver
  - Return success

**3.1.9** Implement score deletion endpoint
- Implement `delete_score(request, score_id)` function
  - Validate authentication (require admin permission)
  - Validate score exists
  - Check score is not already approved (cannot delete approved scores)
  - Soft delete: update status to "deleted"
  - Log deletion in audit trail
  - Return success

**3.1.10** Deploy Response Scorer API
- Create `backend/response_scorer/deploy.sh`
- Deploy to Cloud Functions:
  ```bash
  gcloud functions deploy response-scorer-api \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point response_scorer_handler
  ```
- Update API Gateway to route requests
- Test all endpoints with curl

**3.1.11** Write Response Scorer API tests
- Create `backend/tests/test_response_scorer_api.py`
- Test response retrieval with various filters
- Test score CRUD operations
- Test scoring calculations
- Test permission enforcement
- Test audit trail logging
- Run test suite

---

#### Task Group 3.2: Scoring Algorithm (Days 2-3, 8 hours)

**3.2.1** Design scoring methodology
- Document scoring rules:
  - Weighted scoring: `score = sum(points_awarded * weight)`
  - Point assignment rules:
    - Yes = full points (weight value)
    - Partial = half points (weight / 2)
    - No = zero points
    - Info questions = not scored (weight = "Info")
  - Percentage calculation: `(total_score / max_possible_score) * 100`
  - Letter grade mapping:
    - A: 90-100%
    - B: 80-89%
    - C: 70-79%
    - D: 60-69%
    - F: 0-59%
- Write documentation in `backend/response_scorer/SCORING_METHODOLOGY.md`

**3.2.2** Implement scoring calculator
- Create `backend/response_scorer/scoring_calculator.py`
- Implement `calculate_question_score(answer, weight, input_type)` function
  - Handle answer types:
    - "yes" → full points
    - "no" → zero points
    - "partial" → half points
    - Numeric answer → evaluate against threshold (if specified)
    - Text answer → manual scoring required
  - Return points_awarded and max_points

**3.2.3** Implement automatic scoring
- Implement `auto_score_response(response, template)` function
  - Accept response object and form template (with weights)
  - For each question:
    - Get answer from response
    - Get weight from template
    - Call `calculate_question_score()`
    - Store result
  - Return score object (ready to insert into database)
- This allows one-click scoring for simple responses

**3.2.4** Implement score comparison
- Implement `compare_scores(score_id_1, score_id_2)` function
  - Retrieve both scores
  - Calculate differences:
    - Total score difference
    - Percentage difference
    - Question-by-question comparison
  - Return comparison object
- Useful for comparing vendors or tracking score changes

**3.2.5** Implement scoring statistics
- Implement `calculate_score_statistics(survey_type)` function
  - Query all scores for a survey type
  - Calculate:
    - Average score
    - Median score
    - Standard deviation
    - Score distribution (histogram data)
    - Top performers (top 10%)
  - Return statistics object

**3.2.6** Add score normalization
- Implement `normalize_scores(scores)` function
  - Convert scores to common scale (0-100)
  - Useful when comparing scores across different survey types
  - Handle surveys with different numbers of questions

**3.2.7** Test scoring algorithm
- Create test cases with known answers and weights
- Verify calculations are correct
- Test edge cases:
  - All "yes" answers (should be 100%)
  - All "no" answers (should be 0%)
  - Mix of yes/partial/no
  - Info questions (should not affect score)
  - Missing answers (should not affect max_score denominator)

---

#### Task Group 3.3: Audit Trail & Version Control (Day 3, 4 hours)

**3.3.1** Implement audit logging utility
- Create `backend/common/audit_logger.py`
- Implement `log_audit(entity_type, entity_id, action, user_id, previous_value, new_value, reason)` function
  - Insert record into `scoring.audit_trail`
  - Include timestamp, IP address
  - Support batching (log multiple changes at once)

**3.3.2** Add audit logging to all write operations
- Update `create_score()` → log "created"
- Update `update_score()` → log "updated" with field changes
- Update `delete_score()` → log "deleted"
- Update `submit_score()` → log "submitted"
- Update `create_template()` → log "created"
- Update `deploy_form()` → log "deployed"

**3.3.3** Implement score version history
- Create `scoring.score_versions` table (if not exists):
  - Columns: `version_id`, `score_id`, `version_number`, `data` (JSON), `created_by`, `created_at`
- Before updating a score, save current version
- Implement `get_score_history(score_id)` endpoint
  - Return all versions
  - Allow reverting to previous version

**3.3.4** Create audit trail viewer endpoint
- Implement `get_audit_trail(request)` endpoint (admin only)
  - Query `scoring.audit_trail`
  - Support filtering by entity_type, entity_id, user_id, date_range
  - Return paginated list of audit records
- Display who did what, when, and what changed

---

### Week 6: Response Scorer Frontend

#### Task Group 3.4: Response Scorer UI Foundation (Days 1-2, 12 hours)

**3.4.1** Set up Response Scorer React project
- Create `frontend/response-scorer/` directory
- Initialize React app: `npm create vite@latest response-scorer -- --template react`
- Install dependencies (same as Form Builder)
- Configure Tailwind CSS
- Set up project structure

**3.4.2** Create API client for Response Scorer
- Create `frontend/response-scorer/src/services/responseScorerApi.js`
- Implement API methods:
  - `fetchResponses(filters, pagination)`
  - `fetchResponseDetail(responseId)`
  - `fetchSurveys()`
  - `fetchScores(filters, pagination)`
  - `fetchScoreDetail(scoreId)`
  - `createScore(scoreData)`
  - `updateScore(scoreId, updates)`
  - `deleteScore(scoreId)`
  - `submitScore(scoreId)`
- Add error handling

**3.4.3** Create shared layout
- Create `frontend/response-scorer/src/components/Layout.jsx`
- Header with:
  - Opex logo
  - App title: "Response Scorer"
  - User menu
- Sidebar navigation:
  - Dashboard
  - Responses
  - Scored Responses
  - Analytics (optional)
- Apply Opex branding

**3.4.4** Create dashboard page
- Create `frontend/response-scorer/src/pages/Dashboard.jsx`
- Show key metrics:
  - Total responses
  - Unscored responses
  - Responses in progress
  - Completed scores
  - Average score across all surveys
- Show recent activity (last 10 actions)
- Add quick actions:
  - Score New Response
  - View Unscored Responses

**3.4.5** Create responses list page
- Create `frontend/response-scorer/src/pages/ResponsesList.jsx`
- Display table of all responses:
  - Columns: Company, Survey Type, Source, Submitted Date, Status, Actions
  - Color-code status (unscored, in-progress, completed)
  - Actions: View Details, Score, View Score
- Add filters:
  - By company (text search with autocomplete)
  - By survey type (dropdown)
  - By source (dropdown)
  - By date range (date picker)
  - By status (dropdown)
- Add sorting (by date, company, status)
- Add pagination

**3.4.6** Create advanced filtering panel
- Create `frontend/response-scorer/src/components/FilterPanel.jsx`
- Collapsible filter panel (show/hide)
- Multiple filter fields:
  - Company name (text input with suggestions)
  - Survey type (multi-select dropdown)
  - Source (multi-select dropdown)
  - Date range (start date, end date)
  - Status (multi-select: unscored, in-progress, completed)
  - Scored by (dropdown, admin only)
- Add "Apply Filters" button
- Add "Clear Filters" button
- Show active filters as removable chips

**3.4.7** Implement response search
- Add search bar above responses table
- Search across:
  - Company name
  - Contact email
  - Response ID
- Highlight matching text in results
- Show search result count

**3.4.8** Create response card component (alternative view)
- Create `frontend/response-scorer/src/components/ResponseCard.jsx`
- Display response as card:
  - Company name (large, bold)
  - Survey type badge
  - Submitted date
  - Status badge
  - Score (if completed)
  - Quick actions (Score, View)
- Add grid view option (cards vs table)

---

#### Task Group 3.5: Scoring Interface (Days 2-4, 16 hours)

**3.5.1** Create response detail page
- Create `frontend/response-scorer/src/pages/ResponseDetail.jsx`
- Two-column layout:
  - Left: Response details (metadata + all Q&A)
  - Right: Scoring panel
- Display response metadata:
  - Company name
  - Contact info (name, email, phone)
  - Survey type
  - Submitted date
  - Source
- Display all question-answer pairs:
  - Question text
  - Answer (formatted based on type)
  - Category badge
  - Default weight (from template)

**3.5.2** Create scoring panel
- Create `frontend/response-scorer/src/components/ScoringPanel.jsx`
- Display scoring controls:
  - Overall notes textarea
  - Save Draft button
  - Submit Score button
  - Score summary (running total)
- Show scoring progress:
  - Questions scored / total questions
  - Progress bar
  - Current score / max score
  - Percentage

**3.5.3** Create question scoring component
- Create `frontend/response-scorer/src/components/QuestionScorer.jsx`
- For each question, display:
  - Question text
  - Answer (from response)
  - Weight input (prepopulated, editable)
  - Points awarded input (auto-calculated or manual)
  - Max points (= weight)
  - Comments textarea (optional)
- Auto-calculate points for yes/no/partial answers
- Allow manual override of points
- Add "Mark as Info" option (excludes from score)

**3.5.4** Implement automatic scoring
- Add "Auto-Score" button
- On click, call API to auto-score simple questions (yes/no)
- Populate points_awarded fields
- Leave manual scoring for complex questions (text answers)
- Show toast: "Auto-scoring complete. Review and adjust as needed."

**3.5.5** Implement inline question scoring
- Display questions in expandable accordion
- Click to expand question and score it
- Collapse when done
- Show checkmark icon when scored
- Show warning icon if points > max points

**3.5.6** Add score validation
- Validate before saving:
  - All questions have weights
  - Points awarded ≤ max points for each question
  - No negative points
- Show validation errors inline
- Disable submit until validation passes

**3.5.7** Implement save draft functionality
- Add "Save Draft" button (always visible)
- Save score to database with status "draft"
- Show success toast: "Draft saved"
- Auto-save every 60 seconds (background)
- Show "Last saved: X minutes ago" indicator

**3.5.8** Implement score submission
- Add "Submit Score" button
- Validate score is complete
- Show confirmation modal:
  - Display final score summary
  - Total score / max score
  - Percentage
  - Letter grade
  - "Are you sure?"
- On confirm, call API to submit
- Update status to "submitted"
- Show success message
- Redirect to scored responses list

**3.5.9** Implement score editing
- If user opens an existing score (draft or in-progress):
  - Load score data
  - Populate all fields (weights, points, comments)
  - Allow editing
  - Save updates to existing score (don't create new)
- Show "Editing Score" indicator in header

**3.5.10** Add question notes and comments
- Allow adding detailed comments for each question
- Rich text editor (bold, italic, lists)
- Save comments in `scoring.question_scores` table
- Display comments in score detail view

**3.5.11** Implement score comparison mode
- Add "Compare to Previous Score" option
- If company has been scored before:
  - Load previous score
  - Show side-by-side comparison
  - Highlight differences (improved/declined)
  - Show score change (delta)

**3.5.12** Add scoring keyboard shortcuts
- Tab: Move to next question
- Shift+Tab: Move to previous question
- Ctrl+S: Save draft
- Ctrl+Enter: Submit score
- Display keyboard shortcut help (? key)

---

#### Task Group 3.6: Scored Responses Management (Day 4, 8 hours)

**3.6.1** Create scored responses list page
- Create `frontend/response-scorer/src/pages/ScoredResponsesList.jsx`
- Display table of all scored responses:
  - Columns: Company, Survey Type, Score, Percentage, Letter Grade, Scored By, Scored Date, Status, Actions
  - Color-code scores (green = high, yellow = medium, red = low)
  - Actions: View, Edit, Delete, Export
- Add filters (same as responses list)
- Add sorting by score, date, company
- Add pagination

**3.6.2** Create score detail view page
- Create `frontend/response-scorer/src/pages/ScoreDetail.jsx`
- Display complete score:
  - Company info
  - Survey type
  - Total score, percentage, letter grade
  - Scored by (user name)
  - Scored date
  - Overall notes
  - All question scores (question, answer, weight, points, comments)
- Add action buttons:
  - Edit Score (if status allows)
  - Export Score (PDF)
  - Delete Score (admin only)
  - Compare to Other Scores

**3.6.3** Implement score export to PDF
- Install `jspdf` and `jspdf-autotable`:
  ```bash
  npm install jspdf jspdf-autotable
  ```
- Implement `exportScorePdf(scoreId)` function
- Generate PDF with:
  - Opex logo and branding
  - Company name and score summary
  - Table of all question scores
  - Notes and comments
  - Footer with generation date
- Trigger download on button click

**3.6.4** Create score comparison page
- Create `frontend/response-scorer/src/pages/ScoreComparison.jsx`
- Allow selecting 2+ scores to compare
- Display side-by-side comparison table:
  - Question in column 1
  - Score 1 in column 2
  - Score 2 in column 3
  - Difference (delta) in column 4
- Highlight differences (green = better, red = worse)
- Show overall score comparison at top

**3.6.5** Implement score deletion
- Add "Delete Score" button (admin only)
- Show confirmation modal: "Are you sure? This cannot be undone."
- On confirm, call API to delete
- Remove from list
- Show success toast

**3.6.6** Add bulk score export
- Add "Select" checkbox to each score row
- Add "Export Selected" button
- Generate single PDF with all selected scores
- Or generate ZIP file with individual PDFs

**3.6.7** Create score analytics dashboard (optional)
- Create `frontend/response-scorer/src/pages/Analytics.jsx`
- Show charts and graphs:
  - Score distribution (histogram)
  - Average score by survey type (bar chart)
  - Score trends over time (line chart)
  - Top performers (leaderboard)
- Use chart library (e.g., recharts):
  ```bash
  npm install recharts
  ```

**3.6.8** Test complete scoring workflow
- Select unscored response
- Open response detail
- Score all questions (mix of auto and manual)
- Add comments
- Save draft
- Edit draft
- Submit score
- View submitted score
- Export to PDF
- Verify data in BigQuery

---

#### Task Group 3.7: Testing and Polish (Days 4-5, 8 hours)

**3.7.1** Test complete Response Scorer workflow
- List responses with filters
- View response detail
- Auto-score simple questions
- Manually score complex questions
- Save draft
- Resume draft later
- Submit score
- View scored response
- Export PDF
- Edit existing score
- Delete score
- Compare scores

**3.7.2** Test error scenarios
- Try to score without authentication
- Try to score response outside permission scope
- Try to submit incomplete score
- Test network errors
- Test API errors
- Verify error messages are user-friendly

**3.7.3** Test responsive design
- Test on desktop, tablet, mobile
- Verify scoring interface works on mobile
- Verify tables are scrollable on small screens

**3.7.4** Cross-browser testing
- Test in Chrome, Firefox, Safari, Edge
- Fix browser-specific bugs

**3.7.5** Performance optimization
- Measure page load time
- Lazy load responses (infinite scroll)
- Optimize PDF generation (handle large scores)
- Debounce auto-save (don't save on every keystroke)

**3.7.6** Accessibility improvements
- Keyboard navigation for scoring interface
- Screen reader support
- ARIA labels
- Color contrast

**3.7.7** Add user guidance
- Tooltips explaining scoring methodology
- Help documentation
- Empty states with instructions

**3.7.8** Security audit
- Ensure permission checks work correctly
- Test for XSS vulnerabilities (user input in comments)
- Test for SQL injection (API inputs)
- Test for CSRF (API uses JWT, should be safe)

---

#### Phase 3 Deliverables Checklist

- [ ] Response Scorer API deployed (10+ endpoints)
- [ ] Scoring algorithm implemented and tested
- [ ] Audit trail logging active
- [ ] Response Scorer UI complete
- [ ] Response filtering functional
- [ ] Scoring interface working (manual and auto)
- [ ] Score saving and submission working
- [ ] Scored responses list working
- [ ] Score detail view working
- [ ] PDF export working
- [ ] Score comparison working
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Response Scorer accessible at production URL

---

## Phase 4: Integration & Testing (Weeks 7-8)

**Objective:** Integrate all components, perform end-to-end testing, security audit, and optimization

**Hours:** 48 hours
**Cost:** $1,680 (from Phase 4 budget)
**Dependencies:** Phases 1, 2, and 3 complete

---

### Week 7: Integration and End-to-End Testing

#### Task Group 4.1: Component Integration (Days 1-2, 12 hours)

**4.1.1** Integrate authentication with Form Builder
- Ensure Form Builder uses auth tokens from login
- Test protected routes (redirect to login if not authenticated)
- Test permission enforcement (user can only access forms for their categories)
- Test token refresh (handle expired tokens gracefully)

**4.1.2** Integrate authentication with Response Scorer
- Same tests as Form Builder
- Verify response filtering by permissions works correctly

**4.1.3** Create unified navigation
- Add navigation links between apps:
  - From Form Builder → Response Scorer
  - From Response Scorer → Form Builder
  - From any app → User Profile/Settings
- Add global app switcher in header

**4.1.4** Create unified deployment script
- Create `deploy-all.sh` script
- Deploy all Cloud Functions:
  - auth-api
  - form-builder-api
  - response-scorer-api
- Deploy frontend apps to GitHub Pages:
  - Form Builder
  - Response Scorer
  - Auth UI
- Update API Gateway configuration
- Run deployment validation tests

**4.1.5** Set up production environment
- Create production GCP project (if different from dev)
- Create production BigQuery datasets
- Deploy all schemas to production
- Configure production API Gateway
- Set up production GitHub Pages

**4.1.6** Create environment configuration
- Create `.env.production` files
- Set production API URLs
- Set production BigQuery project/dataset names
- Set production GitHub repository
- Document environment variables

**4.1.7** Test data flow end-to-end
- Create form in Form Builder → Deploy → Fill out form → Submit
- Verify data appears in BigQuery
- Open Response Scorer → Find response → Score it → Submit
- Verify score saved in BigQuery
- Export score to PDF
- Verify all steps work seamlessly

**4.1.8** Test webhook integration
- Create new form with custom questions
- Deploy form
- Submit form multiple times
- Verify webhook creates table correctly
- Verify all submissions appear in BigQuery
- Verify responses appear in Response Scorer

**4.1.9** Test permission-based data access
- Create test users with different permissions:
  - User A: view only, company X, category Y
  - User B: edit, company X, all categories
  - User C: admin, all companies
- Login as each user
- Verify User A can view but not edit
- Verify User B can view and edit
- Verify User C can do everything
- Verify users only see data for their assigned companies/categories

**4.1.10** Test form versioning and re-deployment
- Create form, deploy (version 1)
- Edit form (add question, change weight)
- Re-deploy (version 2)
- Verify version 1 responses are preserved
- Verify new responses use version 2
- Verify backward compatibility

---

#### Task Group 4.2: End-to-End Testing (Days 2-3, 12 hours)

**4.2.1** Create automated E2E test suite
- Set up Playwright or Cypress:
  ```bash
  npm install -D @playwright/test
  ```
- Create test specs:
  - `tests/e2e/auth.spec.js` - Authentication flow
  - `tests/e2e/form-builder.spec.js` - Form Builder flow
  - `tests/e2e/response-scorer.spec.js` - Response Scorer flow
  - `tests/e2e/integration.spec.js` - Full integration flow

**4.2.2** Write authentication E2E tests
- Test user registration
- Test login
- Test logout
- Test password reset
- Test token refresh
- Test session expiration
- Test concurrent sessions

**4.2.3** Write Form Builder E2E tests
- Test create new template
- Test add questions from database
- Test question customization (weights, input types)
- Test reorder questions
- Test save draft
- Test form preview
- Test form deployment
- Test edit existing template

**4.2.4** Write Response Scorer E2E tests
- Test list responses with filters
- Test view response detail
- Test auto-score
- Test manual scoring
- Test save draft score
- Test edit draft score
- Test submit score
- Test view scored response
- Test export to PDF
- Test score comparison

**4.2.5** Write integration E2E test
- Test complete workflow:
  1. Register new user
  2. Login
  3. Create form template
  4. Deploy form
  5. Fill out deployed form (headless browser)
  6. Wait for data in BigQuery
  7. Score response in Response Scorer
  8. Export score to PDF
  9. Verify PDF contains correct data
- This is the ultimate test - if this passes, the system works!

**4.2.6** Run E2E tests in CI/CD
- Set up GitHub Actions workflow
- Run E2E tests on every commit to main
- Run E2E tests before deployment
- Generate test reports
- Fail deployment if tests fail

**4.2.7** Test error recovery
- Test what happens when BigQuery is down (simulate with invalid credentials)
- Test what happens when GitHub API is down
- Test what happens when network is slow
- Test what happens when API returns 500 error
- Verify error messages are shown
- Verify user can retry

**4.2.8** Test data consistency
- Submit form
- Verify data matches in all views:
  - Raw table in `opex_dev`
  - Unpivoted view in `scoring.all_survey_responses`
  - Response Scorer UI
- Verify no data loss or corruption

**4.2.9** Load testing
- Use Apache Bench or Locust to simulate load:
  ```bash
  ab -n 1000 -c 10 https://api-url/response-scorer/responses
  ```
- Test API endpoints under load
- Target: 100 concurrent users, < 2s response time
- Identify bottlenecks
- Optimize slow queries

**4.2.10** Stress testing
- Test with large datasets:
  - 10,000+ responses
  - 1,000+ questions in database
  - 100+ form templates
- Verify pagination works correctly
- Verify queries are performant
- Add database indexes if needed

---

#### Task Group 4.3: Security Audit (Day 3-4, 8 hours)

**4.3.1** Conduct authentication security review
- Test JWT token security:
  - Verify signature cannot be forged
  - Verify token expiration is enforced
  - Verify token cannot be reused after logout
  - Test token in URL (should be rejected)
- Test password security:
  - Verify passwords are hashed (not plaintext)
  - Verify bcrypt rounds (should be ≥12)
  - Test weak passwords (should be rejected)
  - Test password reuse (should be allowed)
- Test brute force protection:
  - Attempt 10 failed logins
  - Verify account is locked
  - Verify CAPTCHA is shown (if implemented)

**4.3.2** Test authorization and permissions
- Test horizontal privilege escalation:
  - User A tries to access User B's data
  - Should be blocked with 403
- Test vertical privilege escalation:
  - Non-admin tries to access admin endpoints
  - Should be blocked with 403
- Test permission bypass:
  - Try to access data without token
  - Try to access data with expired token
  - Try to access data with manipulated token (change user_id)
- All should be blocked with 401/403

**4.3.3** Test for injection vulnerabilities
- Test SQL injection:
  - Try injecting SQL in search queries: `' OR '1'='1`
  - Verify BigQuery parameterized queries prevent injection
- Test XSS (Cross-Site Scripting):
  - Try injecting JavaScript in comments: `<script>alert('XSS')</script>`
  - Verify output is sanitized/escaped
  - Test stored XSS (save malicious input, view later)
- Test command injection:
  - Try injecting shell commands in file paths: `; rm -rf /`
  - Should be blocked or sanitized

**4.3.4** Test for CSRF (Cross-Site Request Forgery)
- API uses JWT tokens in Authorization header
- JWT in header prevents CSRF (cannot be sent cross-origin by browser)
- Verify cookies are not used for authentication
- If cookies used, add CSRF token

**4.3.5** Test API rate limiting
- Send 1000 requests to API in 1 minute
- Verify rate limit is enforced (429 response after threshold)
- Verify legitimate users are not blocked
- Test rate limit bypass attempts (change IP, user agent)

**4.3.6** Test input validation
- Test all API endpoints with invalid inputs:
  - Missing required fields
  - Wrong data types (string instead of number)
  - Excessively long strings (> 10,000 chars)
  - Negative numbers where positive expected
  - Invalid email formats
  - Invalid JSON
- Verify all return 400 with helpful error messages
- Verify no sensitive info leaked in errors

**4.3.7** Test file upload security (if applicable)
- If forms allow file uploads:
  - Test malicious file types (.exe, .sh, .js)
  - Test oversized files (> 100MB)
  - Test filename injection: `../../etc/passwd`
  - Verify files are scanned for malware
  - Verify files are stored securely (not in web root)

**4.3.8** Review secrets management
- Verify no secrets in code (API keys, passwords)
- Verify secrets stored in Cloud Secret Manager
- Verify secrets not logged
- Verify secrets not returned in API responses
- Rotate all secrets (test rotation process)

**4.3.9** Test HTTPS and TLS
- Verify all API endpoints use HTTPS (not HTTP)
- Verify TLS version ≥ 1.2
- Verify strong cipher suites
- Test SSL certificate validity
- Use SSL Labs test: https://www.ssllabs.com/ssltest/

**4.3.10** Security documentation
- Document all security measures
- Document threat model
- Document known limitations
- Document incident response plan
- Document security testing results

---

### Week 8: Performance Optimization and Final Testing

#### Task Group 4.4: Performance Optimization (Days 1-2, 12 hours)

**4.4.1** Optimize BigQuery queries
- Review all SQL queries
- Add missing indexes:
  - Index on `company_name` in response tables
  - Index on `survey_type` in all_survey_responses
  - Index on `user_id` in auth tables
  - Composite index on `(company_name, timestamp)` for filtering
- Use query caching where appropriate
- Partition large tables by date (if > 1M rows)
- Use clustering for common filter fields

**4.4.2** Optimize API response times
- Measure baseline (use Cloud Trace)
- Identify slow endpoints (p95 > 2s)
- Optimize slow queries
- Add caching layer:
  - Cache question database (rarely changes)
  - Cache user permissions (5 min TTL)
  - Cache survey list (1 min TTL)
- Use Redis or Cloud Memorystore for caching
- Implement cache invalidation

**4.4.3** Optimize frontend bundle size
- Analyze bundle size: `npm run build && npx vite-bundle-visualizer`
- Identify large dependencies
- Lazy load routes (code splitting):
  ```javascript
  const ResponseScorer = lazy(() => import('./pages/ResponseScorer'))
  ```
- Tree-shake unused code
- Minify JavaScript and CSS
- Target bundle size < 500KB (gzipped)

**4.4.4** Optimize images and assets
- Compress Opex logo (use WebP format)
- Use responsive images (srcset)
- Lazy load images below the fold
- Use CDN for static assets (Cloud Storage)
- Enable browser caching (Cache-Control headers)

**4.4.5** Implement pagination optimization
- Use cursor-based pagination (instead of offset)
- Implement infinite scroll (better UX than page numbers)
- Prefetch next page in background
- Show loading skeleton while fetching

**4.4.6** Add loading optimizations
- Show skeleton screens (instead of blank page)
- Use optimistic UI updates (update UI immediately, sync later)
- Debounce search inputs (wait 300ms after typing stops)
- Throttle scroll events (use intersection observer)

**4.4.7** Optimize form preview
- Debounce preview updates (500ms)
- Cache generated HTML (5 min)
- Use iframe for preview (prevent conflicts)
- Add preview refresh button (manual control)

**4.4.8** Optimize PDF generation
- Generate PDFs server-side (not client-side)
- Create PDF generation Cloud Function
- Cache generated PDFs (24 hours)
- Stream PDF download (don't load entire file in memory)

**4.4.9** Database connection pooling
- Implement connection pooling for BigQuery
- Reuse connections across requests
- Set max pool size (10 connections)
- Set connection timeout (30 seconds)

**4.4.10** Measure performance improvements
- Re-run load tests
- Compare before/after metrics:
  - API response times (p50, p95, p99)
  - Page load times
  - Time to interactive
  - Bundle size
- Document improvements

---

#### Task Group 4.5: User Acceptance Testing (Days 2-3, 8 hours)

**4.5.1** Prepare UAT environment
- Set up UAT environment (separate from prod)
- Load UAT with realistic data (100+ responses)
- Create UAT user accounts
- Document UAT process

**4.5.2** Recruit UAT testers
- Identify 3-5 Opex Technologies users
- Different roles:
  - Form creator (will use Form Builder)
  - Scorer (will use Response Scorer)
  - Admin (will manage users and permissions)
- Schedule UAT sessions

**4.5.3** Conduct UAT sessions
- Provide UAT script with tasks:
  - Task 1: Create a new survey form
  - Task 2: Deploy form and test it
  - Task 3: Score a response
  - Task 4: View and export scored response
  - Task 5: Manage user permissions (admin only)
- Observe users (note friction points)
- Collect feedback (survey or interview)

**4.5.4** Document UAT feedback
- Create issue for each piece of feedback
- Categorize: bug, usability issue, feature request, nice-to-have
- Prioritize: must-fix, should-fix, could-fix, won't-fix
- Assign to team members

**4.5.5** Fix critical issues from UAT
- Fix all "must-fix" bugs
- Improve usability issues
- Re-test with users if significant changes

**4.5.6** UAT sign-off
- Get formal approval from stakeholders
- Document UAT results
- Sign-off on deliverables

---

#### Task Group 4.6: Documentation (Days 3-4, 8 hours)

**4.6.1** Write technical architecture documentation
- Create `docs/ARCHITECTURE.md`
- Document:
  - System overview
  - Component diagram
  - Data flow diagram
  - Technology stack
  - Infrastructure setup
  - Security architecture
- Include diagrams (use draw.io or similar)

**4.6.2** Write API documentation
- Create `docs/API_REFERENCE.md`
- Document all API endpoints:
  - URL
  - HTTP method
  - Authentication required
  - Request parameters
  - Request body schema
  - Response schema
  - Error codes
  - Example curl commands
- Use OpenAPI/Swagger format
- Generate interactive API docs (Swagger UI)

**4.6.3** Write user guide for Form Builder
- Create `docs/FORM_BUILDER_GUIDE.md`
- Step-by-step instructions:
  - How to create a form
  - How to select questions
  - How to customize weights
  - How to preview a form
  - How to deploy a form
  - How to edit a form
  - How to share a form
- Include screenshots
- Add troubleshooting section

**4.6.4** Write user guide for Response Scorer
- Create `docs/RESPONSE_SCORER_GUIDE.md`
- Step-by-step instructions:
  - How to find a response
  - How to filter responses
  - How to score a response
  - How to save a draft
  - How to submit a score
  - How to view scored responses
  - How to export to PDF
  - How to compare scores
- Include screenshots
- Add troubleshooting section

**4.6.5** Write administrator guide
- Create `docs/ADMIN_GUIDE.md`
- Administrator tasks:
  - How to create users
  - How to assign permissions
  - How to revoke permissions
  - How to manage question database
  - How to view audit trail
  - How to monitor system health
  - How to troubleshoot issues
  - How to backup data
  - How to restore data

**4.6.6** Write deployment guide
- Create `docs/DEPLOYMENT.md`
- Deployment process:
  - Prerequisites (GCP account, GitHub account)
  - Environment setup
  - Cloud Function deployment
  - Frontend deployment
  - Database schema deployment
  - API Gateway configuration
  - DNS configuration (if custom domain)
  - Monitoring setup
  - Post-deployment verification

**4.6.7** Write developer onboarding guide
- Create `docs/DEVELOPER_ONBOARDING.md`
- Getting started:
  - Clone repository
  - Install dependencies
  - Set up local environment
  - Run locally
  - Run tests
  - Code style guide
  - Git workflow
  - Deployment process

**4.6.8** Create video tutorials
- Record screen capture videos (2 hours total):
  - Video 1: Form Builder tutorial (30 min)
  - Video 2: Response Scorer tutorial (30 min)
  - Video 3: Admin tasks tutorial (30 min)
  - Video 4: System overview and architecture (30 min)
- Edit videos (add captions, branding)
- Upload to YouTube or Vimeo (private/unlisted)
- Link from documentation

---

#### Phase 4 Deliverables Checklist

- [ ] All components integrated
- [ ] End-to-end tests passing
- [ ] Security audit complete (no critical issues)
- [ ] Performance optimized (p95 < 2s)
- [ ] Load testing passed (100 concurrent users)
- [ ] UAT completed and signed off
- [ ] All documentation written
- [ ] Video tutorials recorded
- [ ] System ready for production deployment

---

## Phase 5: Deployment & Training (Week 9)

**Objective:** Deploy to production, train users, and provide post-launch support

**Hours:** 24 hours
**Cost:** Included in Phase 4 budget
**Dependencies:** Phase 4 complete and UAT approved

---

### Week 9: Production Deployment and Launch

#### Task Group 5.1: Pre-Deployment Preparation (Day 1, 4 hours)

**5.1.1** Create deployment checklist
- Document all deployment steps
- Assign owners for each step
- Define rollback plan
- Define success criteria

**5.1.2** Backup production data
- Export all existing BigQuery tables
- Store backups in Cloud Storage
- Document backup location
- Test restore procedure

**5.1.3** Schedule deployment window
- Choose low-traffic time (weekend or evening)
- Notify all stakeholders
- Plan for 4-hour deployment window
- Arrange on-call support

**5.1.4** Prepare rollback plan
- Document rollback steps:
  1. Revert Cloud Functions to previous version
  2. Revert frontend deployments
  3. Revert database schema changes (if any)
  4. Restore data from backup (if needed)
- Test rollback in staging environment

---

#### Task Group 5.2: Production Deployment (Day 1, 4 hours)

**5.2.1** Deploy database schema to production
- Run `database/deploy_schemas.py` on production
- Verify all tables created successfully
- Run migration scripts (Question Database, etc.)
- Verify data integrity

**5.2.2** Deploy Cloud Functions to production
- Deploy auth-api
- Deploy form-builder-api
- Deploy response-scorer-api
- Verify all functions are running
- Test each API endpoint with curl

**5.2.3** Deploy API Gateway to production
- Update API Gateway configuration
- Deploy new configuration
- Verify routing works correctly
- Test rate limiting

**5.2.4** Deploy frontend applications to production
- Build production bundles:
  ```bash
  cd frontend/form-builder && npm run build
  cd frontend/response-scorer && npm run build
  cd frontend/auth-ui && npm run build
  ```
- Deploy to GitHub Pages or Cloud Storage
- Verify all apps are accessible
- Test navigation between apps

**5.2.5** Configure DNS (if custom domain)
- Point form-builder.opextechnologies.com to GitHub Pages
- Point response-scorer.opextechnologies.com to GitHub Pages
- Point api.opextechnologies.com to API Gateway
- Verify DNS propagation (may take hours)
- Configure SSL certificates

**5.2.6** Create initial admin user
- Run seed script to create admin account
- Test login with admin credentials
- Grant admin permissions
- Document admin credentials (store securely)

**5.2.7** Run smoke tests
- Test authentication (login, logout)
- Test Form Builder (create, deploy form)
- Test Response Scorer (score response)
- Test all critical paths
- Verify no errors in logs

**5.2.8** Monitor deployment
- Watch Cloud Logging for errors
- Watch API Gateway metrics
- Watch BigQuery usage
- Watch for user reports

---

#### Task Group 5.3: User Training (Days 2-3, 8 hours)

**5.3.1** Prepare training materials
- Finalize user guides
- Create training slide deck (PowerPoint or Google Slides)
- Set up training environment (demo data)
- Prepare handouts (quick reference cards)

**5.3.2** Schedule training sessions
- Schedule 3 training sessions (1 hour each):
  - Session 1: Form Builder training
  - Session 2: Response Scorer training
  - Session 3: Admin training
- Send calendar invites to all users
- Record sessions for later viewing

**5.3.3** Conduct Form Builder training
- Agenda:
  - Introduction to Form Builder (10 min)
  - Live demo: Create a form (15 min)
  - Hands-on exercise: Users create their own form (20 min)
  - Q&A (15 min)
- Share screen and walk through:
  - Login
  - Navigate to Form Builder
  - Select questions from database
  - Customize weights
  - Preview form
  - Deploy to GitHub
  - Share deployed form URL
- Help users complete hands-on exercise
- Answer questions

**5.3.4** Conduct Response Scorer training
- Agenda:
  - Introduction to Response Scorer (10 min)
  - Live demo: Score a response (15 min)
  - Hands-on exercise: Users score a response (20 min)
  - Q&A (15 min)
- Share screen and walk through:
  - Login
  - Navigate to Response Scorer
  - Filter responses
  - Open response detail
  - Auto-score simple questions
  - Manually score complex questions
  - Add comments
  - Save draft
  - Submit score
  - Export to PDF
- Help users complete hands-on exercise
- Answer questions

**5.3.5** Conduct Admin training (admins only)
- Agenda:
  - Introduction to admin features (10 min)
  - User management demo (15 min)
  - Permission management demo (15 min)
  - Monitoring and troubleshooting (10 min)
  - Q&A (10 min)
- Cover:
  - Creating new users
  - Assigning permissions (view, edit, admin)
  - Revoking permissions
  - Viewing audit trail
  - Monitoring API usage
  - Viewing logs
  - Common troubleshooting scenarios

**5.3.6** Create training recordings
- Edit recorded sessions
- Add captions for accessibility
- Upload to company intranet or YouTube
- Share links with all users

**5.3.7** Distribute documentation
- Share user guides (PDFs)
- Share quick reference cards
- Share video tutorial links
- Create FAQ document (based on training questions)

---

#### Task Group 5.4: Post-Launch Support (Days 3-5, 8 hours)

**5.4.1** Set up support channels
- Create dedicated Slack channel: #opex-form-scorer-support
- Set up email alias: support@daytanalytics.com
- Create issue tracking board (Jira or GitHub Issues)
- Define SLAs (24-hour response time)

**5.4.2** Monitor system health
- Check Cloud Monitoring dashboards daily
- Review error logs
- Monitor API usage (watch for spikes)
- Monitor BigQuery costs
- Set up alerts for anomalies

**5.4.3** Handle user questions and issues
- Respond to support requests within 24 hours
- Troubleshoot issues (check logs, reproduce bug)
- Provide workarounds if immediate fix not possible
- Escalate critical issues
- Track all issues in issue tracker

**5.4.4** Fix critical bugs (hot fixes)
- Triage reported bugs (critical, high, medium, low)
- Fix critical bugs immediately (deploy within 24 hours)
- Test fixes in staging before deploying to production
- Notify users when fix is deployed

**5.4.5** Collect user feedback
- Send post-launch survey to all users (after 1 week)
- Questions:
  - How easy is the system to use? (1-5)
  - What features do you use most?
  - What features are missing?
  - What improvements would you suggest?
  - Would you recommend this system? (NPS)
- Analyze feedback
- Prioritize feature requests

**5.4.6** Update documentation based on feedback
- Add new FAQ entries
- Update user guides if confusion identified
- Create additional tutorials for complex features
- Improve error messages if users confused

**5.4.7** Conduct retrospective
- Meet with project team
- Discuss what went well
- Discuss what could be improved
- Document lessons learned
- Plan for future enhancements

**5.4.8** Handover to client
- Transfer ownership of code repositories
- Transfer ownership of GCP project (or grant admin access)
- Transfer documentation
- Provide final invoice
- Schedule follow-up meeting (30 days post-launch)

---

#### Phase 5 Deliverables Checklist

- [ ] Production deployment completed successfully
- [ ] All smoke tests passing
- [ ] DNS configured (if applicable)
- [ ] Initial admin user created
- [ ] 3 training sessions conducted
- [ ] Training recordings distributed
- [ ] Documentation distributed
- [ ] Support channels set up
- [ ] Post-launch monitoring active
- [ ] User feedback collected
- [ ] Critical bugs fixed
- [ ] Project handover complete
- [ ] 60-day support period begins

---

## Dependencies & Critical Path

### Critical Path (Longest Sequence of Dependent Tasks)

```
Phase 1: Auth (2 weeks)
  ↓
Phase 2: Form Builder (2 weeks) [depends on Auth]
  ↓
Phase 4: Integration (2 weeks) [depends on Form Builder + Response Scorer]
  ↓
Phase 5: Deployment (1 week) [depends on Integration]
```

```
Phase 1: Auth (2 weeks)
  ↓
Phase 3: Response Scorer (2 weeks) [depends on Auth]
```

**Total Critical Path:** 9 weeks

**Note:** Phase 2 (Form Builder) and Phase 3 (Response Scorer) can be developed IN PARALLEL after Phase 1 (Auth) is complete. This saves 2 weeks vs sequential development.

### Task Dependencies

**Cannot start until complete:**
- All of Phase 2 depends on Phase 1 authentication
- All of Phase 3 depends on Phase 1 authentication
- Form Builder deployment (2.3) depends on Form Builder UI (2.4)
- Response Scorer scoring interface (3.5) depends on Response Scorer API (3.1)
- Phase 4 integration depends on Phases 1, 2, and 3 complete
- Phase 5 deployment depends on Phase 4 complete

**Can work in parallel:**
- Form Builder backend (2.1, 2.2) and Form Builder frontend (2.4, 2.5) can be developed simultaneously by different developers
- Response Scorer backend (3.1, 3.2) and Response Scorer frontend (3.4, 3.5) can be developed simultaneously
- Documentation (4.6) can be written while testing (4.2) is in progress

---

## Risk Mitigation

### High-Risk Areas

**1. GitHub API Integration (2.3)**
- **Risk:** GitHub API has rate limits, may fail during deployment
- **Mitigation:**
  - Implement retry logic with exponential backoff
  - Cache GitHub API responses
  - Use authenticated API (higher rate limit)
  - Test thoroughly in staging
  - Have manual deployment fallback (download HTML, upload manually)

**2. BigQuery Performance (all phases)**
- **Risk:** Queries may be slow with large datasets (10,000+ responses)
- **Mitigation:**
  - Add indexes early
  - Partition large tables by date
  - Use materialized views for common queries
  - Test with realistic data volumes
  - Monitor query performance in production

**3. Authentication Security (1.5)**
- **Risk:** Security vulnerabilities could expose user data
- **Mitigation:**
  - Use industry-standard libraries (bcrypt, PyJWT)
  - Follow OWASP best practices
  - Conduct security audit (4.3)
  - Implement rate limiting
  - Use short token expiration (24 hours)
  - Implement security headers (CORS, CSP, etc.)

**4. User Adoption (5.3)**
- **Risk:** Users may not adopt new system, continue using old manual process
- **Mitigation:**
  - Involve users early (UAT)
  - Provide thorough training
  - Create excellent documentation
  - Provide ongoing support
  - Make system intuitive (good UX)
  - Show clear value proposition (time savings)

**5. Data Migration (1.3)**
- **Risk:** Question Database migration may fail or corrupt data
- **Mitigation:**
  - Backup CSV before migration
  - Validate data after migration
  - Compare record counts
  - Spot-check random samples
  - Have rollback plan

### Medium-Risk Areas

**6. Responsive Design (all frontend tasks)**
- **Risk:** UI may not work well on mobile devices
- **Mitigation:**
  - Use mobile-first design approach
  - Test on real devices (not just browser emulation)
  - Use responsive framework (Tailwind CSS)
  - Test touch interactions (drag-and-drop)

**7. Browser Compatibility**
- **Risk:** System may not work in older browsers
- **Mitigation:**
  - Test in all major browsers (Chrome, Firefox, Safari, Edge)
  - Use transpilation (Babel) for older JavaScript support
  - Provide minimum browser version requirements
  - Graceful degradation for unsupported features

**8. Form Preview Performance (2.2.7)**
- **Risk:** Real-time preview may be slow or laggy
- **Mitigation:**
  - Debounce preview updates (500ms)
  - Cache generated HTML
  - Use web workers for HTML generation (if needed)
  - Provide manual refresh option

---

## Success Criteria

**Project will be considered successful if:**

1. **Functional Requirements Met:**
   - [ ] Users can create forms without coding
   - [ ] Forms can be deployed to GitHub Pages with one click
   - [ ] Deployed forms collect data to BigQuery via webhook
   - [ ] Users can view and filter all survey responses
   - [ ] Users can score responses with weighted questions
   - [ ] Scores are saved with complete audit trail
   - [ ] Users can export scores to PDF
   - [ ] Authentication and permissions work correctly

2. **Performance Requirements Met:**
   - [ ] API response times < 2 seconds (p95)
   - [ ] Page load times < 3 seconds
   - [ ] System handles 100 concurrent users
   - [ ] Form deployment completes within 2 minutes

3. **Quality Requirements Met:**
   - [ ] All automated tests passing (unit + E2E)
   - [ ] No critical security vulnerabilities
   - [ ] No critical bugs in production
   - [ ] Code coverage > 70%
   - [ ] Accessibility (WCAG AA compliance)

4. **User Satisfaction:**
   - [ ] UAT sign-off obtained
   - [ ] Post-launch survey NPS > 8
   - [ ] Users successfully trained (can use system independently)
   - [ ] 90% of users adopt system within 30 days

5. **Documentation:**
   - [ ] All technical documentation complete
   - [ ] All user guides complete
   - [ ] API documentation complete
   - [ ] Video tutorials recorded

6. **Business Value:**
   - [ ] 90% reduction in form creation time (vs manual HTML coding)
   - [ ] 100% audit trail for scoring activities
   - [ ] Zero developer intervention required for form deployment
   - [ ] System scales to 10,000+ submissions/month

---

## Conclusion

This implementation plan provides a comprehensive, task-by-task breakdown of the entire Form Builder & Response Scoring System project. With **200+ granular tasks** sequenced for optimal efficiency, the plan ensures:

- **Clear dependencies** - Blocking tasks identified, parallel work maximized
- **Minimal waste** - Efficient sequencing avoids rework
- **Concrete milestones** - Each phase has clear deliverables and success criteria
- **Risk mitigation** - High-risk areas identified with mitigation strategies
- **Testability** - Testing integrated throughout (not bolted on at end)
- **User focus** - UAT and training integrated into plan

**Estimated Effort:** 236 hours over 9 weeks
**Budget:** $16,500
**Team:** 2-3 developers working in parallel can complete in 9 weeks

**Next Steps:**
1. Review this plan with stakeholders
2. Allocate resources (assign developers)
3. Set up project management tools (Jira, Asana, or similar)
4. Begin Phase 1: Infrastructure & Authentication

---

**Document Version:** 1.0
**Last Updated:** November 1, 2025
**Author:** Dayta Analytics / Claude Code
**Status:** Ready for Execution
