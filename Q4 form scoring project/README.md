# Q4 Form Scoring Project

**Form Builder & Response Scoring System**

## Project Overview

This project delivers a comprehensive form management ecosystem that empowers Opex Technologies to create dynamic survey forms, manage response scoring, and leverage advanced analytics capabilities. Building upon existing BigQuery data infrastructure, this solution modernizes survey operations with robust authentication, intuitive user interfaces, and automated deployment workflows.

**Status:** In Development
**Start Date:** August 21, 2025
**Duration:** 9 weeks
**Budget:** $16,500

---

## Key Business Benefits

- Dynamic form creation without developer intervention
- Centralized response scoring with audit trails
- Role-based access control for secure multi-user operations
- Automated deployment to GitHub Pages
- Real-time analytics integration with existing BigQuery infrastructure
- 2x productivity gain in survey management workflows

---

## Project Scope

### 1. Form Builder Application

Interactive web application for creating and managing survey forms:

- Category-based question selection from master question database
- Real-time form preview with Opex branding
- One-click deployment to GitHub Pages
- Automatic webhook configuration for response collection
- Question weight customization for scoring calculations

### 2. Response Scorer Application

Comprehensive dashboard for viewing and scoring survey responses:

- Advanced filtering by company, source, timestamp, and status
- Interactive scoring interface with prepopulated weights
- Detailed notes and comments for each question
- Edit and resubmit capabilities for scored responses
- Complete audit trail for all scoring activities

### 3. Authentication & Security System

Enterprise-grade authentication and authorization:

- Secure login system with JWT token authentication
- Role-based permissions (view, edit, admin)
- Company and category-level access controls
- Session management with automatic timeout
- Password reset and account management features

---

## Technical Architecture

### Frontend Stack

- React/Vue.js for interactive UIs
- GitHub Pages for static hosting
- Responsive design with mobile support
- JWT-based authentication
- Real-time form preview

### Backend Stack

- Google Cloud Functions (Python 3.10+)
- BigQuery for all data storage
- API Gateway for centralized management
- Cloud Storage for static assets
- GitHub API integration

### Data Flow

```
User → Login Page → auth-api → Validate credentials → Issue JWT
  ↓
Store JWT in browser
  ↓
Form Builder UI → API Gateway → form-builder-api → BigQuery (JWT in header)
  ↓
Generate HTML form
  ↓
GitHub API → Deploy to GitHub Pages
  ↓
Generated Form → Existing webhook → BigQuery

Response Scorer UI → API Gateway → response-scorer-api → BigQuery (JWT in header)
```

All API calls: JWT validation → Permission check → Execute request

---

## Database Schema

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **Provider Table** | Store provider information | id, category, name, logo_url |
| **Question Table** | Master question repository | id, category, text, default_weight, tags |
| **Client Table** | Client information | id, category, name, logo_url |
| **Users Table** | Authentication data | id, email, password_hash, last_login |
| **Permission Groups** | Access control | user_id, company, category, permission_level |

---

## Deliverables

### Applications
- Form Builder web application with GitHub deployment
- Response Scorer web application with editing capabilities
- Secure authentication system with role-based permissions
- API Gateway with rate limiting and monitoring
- Automated CI/CD pipeline for updates

### Database & Infrastructure
- Complete BigQuery schema implementation
- Cloud Functions for all backend operations
- Secure API endpoints with authentication
- Monitoring and alerting configuration
- Backup and disaster recovery procedures

### Documentation & Training
- Technical architecture documentation
- API documentation with examples
- User guides for both applications
- Administrator guide for permission management
- Video training sessions (2 hours)
- 60-day post-launch support

---

## Timeline & Milestones

### Weeks 1-2: Infrastructure & Authentication
- Database schema
- Authentication system
- API Gateway setup
- Permission framework

### Weeks 3-4: Form Builder Development
- UI development
- Question management
- Form generation
- GitHub integration

### Weeks 5-6: Response Scorer Development
- Dashboard creation
- Scoring interface
- Edit functionality
- Audit trails

### Weeks 7-8: Integration & Testing
- End-to-end testing
- Performance optimization
- Security audit
- Documentation

### Week 9: Deployment & Training
- Production deployment
- User training
- Handover
- Support initiation

---

## Project Phases & Pricing

### Phase 1: Core Infrastructure & Authentication ($4,240)
- Authentication System (JWT, login) - 24 hours @ $75/hr
- BigQuery Schema & Tables - 16 hours @ $75/hr
- API Gateway Setup - 8 hours @ $75/hr
- Login/Auth UI Components - 16 hours @ $40/hr

### Phase 2: Form Builder Application ($7,200)
- Form Builder API (CRUD operations) - 32 hours @ $75/hr
- Form Builder UI - 48 hours @ $75/hr
- GitHub API Integration - 16 hours @ $75/hr

### Phase 3: Response Scorer Application ($4,800)
- Response Scorer API - 24 hours @ $75/hr
- Response Scorer UI - 40 hours @ $75/hr

### Phase 4: Testing & Documentation ($480)
- Testing & Documentation - 12 hours @ $40/hr

**Total Hours:** 236
**Project Total:** $16,500

---

## Infrastructure Costs (Monthly Estimate)

- Google Cloud Functions: ~$20-40/month
- BigQuery Storage: ~$10-20/month (incremental)
- API Gateway: ~$10-15/month
- GitHub Pages: Free

**Estimated Monthly Total:** $40-75

---

## Payment Schedule

1. **25%** - Project initiation and contract signing ($4,125)
2. **25%** - Completion of Phase 1: Infrastructure & Authentication ($4,125)
3. **25%** - Completion of Phase 2: Form Builder Application ($4,125)
4. **25%** - Completion of Phase 3: Response Scorer & Final Delivery ($4,125)

---

## Success Metrics

### Expected Business Impact

- 90% reduction in form creation time
- 100% audit trail for all scoring activities
- Zero developer intervention for form deployment
- Sub-second response times for all operations
- 99.9% uptime with automated monitoring
- Scalable to 10,000+ submissions per month

---

## Development Standards

### Security
- All code delivered with comprehensive documentation
- Security audit and penetration testing included
- JWT-based authentication with secure token management
- Role-based access control (RBAC)

### Quality Assurance
- 90-day warranty on development work
- End-to-end testing
- Performance optimization
- Code ownership transferred upon final payment

### Support
- 60-day post-launch support included
- 24-hour response time for critical issues
- Weekly progress calls and status updates
- Monthly system health reports

---

## Project Management

- Weekly progress calls and status updates
- Dedicated project manager and technical lead
- Change request process for scope modifications
- Dedicated Slack/email channel for communication

---

## Contact Information

**Project Lead:** Landon Colvig
**Email:** landon@daytanalytics.com
**Phone:** (928) 715-3039

**Dayta Analytics**
719 Pickled Pepper Place
Henderson, NV 89011
Website: daytanalytics.com

---

## Getting Started

### Prerequisites
- Google Cloud Platform account with BigQuery enabled
- GitHub account with Pages enabled
- Node.js 16+ for local development
- Python 3.10+ for backend development

### Development Setup
```bash
# Clone the repository
git clone https://github.com/landoncolvig/opex-technologies.git

# Navigate to project folder
cd "Q4 form scoring project"

# Install dependencies (once frontend is set up)
npm install

# Set up environment variables
cp .env.example .env
```

### Environment Variables
```
GOOGLE_CLOUD_PROJECT=opex-data-lake-k23k4y98m
BIGQUERY_DATASET=your_dataset
JWT_SECRET=your_secret_key
GITHUB_TOKEN=your_github_token
API_GATEWAY_URL=your_api_url
```

---

## Documentation Links

- [Technical Architecture](./docs/architecture.md) (Coming soon)
- [API Documentation](./docs/api.md) (Coming soon)
- [User Guide - Form Builder](./docs/form-builder-guide.md) (Coming soon)
- [User Guide - Response Scorer](./docs/response-scorer-guide.md) (Coming soon)
- [Admin Guide](./docs/admin-guide.md) (Coming soon)

---

## License

Proprietary - Opex Technologies
All rights reserved.

---

**Last Updated:** November 1, 2025
**Proposal Date:** August 21, 2025
**Proposal Valid:** 30 days from submission
