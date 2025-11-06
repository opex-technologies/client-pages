# Form Builder Backend → Frontend Handoff

**Date**: November 6, 2025
**Backend Version**: 1.1.0
**Status**: ✅ Ready for Frontend Integration
**Backend Team**: Dayta Analytics
**Frontend Team**: TBD

---

## 🎯 Executive Summary

The Form Builder API backend is **complete, tested, and deployed**. All 9 endpoints are operational and ready for frontend integration. This document provides everything the frontend team needs to begin development.

**What's Ready**:
- ✅ Complete REST API with 9 endpoints
- ✅ GitHub Pages deployment integration
- ✅ Form generation from templates
- ✅ Question database with 1,041 questions
- ✅ JWT authentication integration
- ✅ Comprehensive documentation
- ✅ Working examples and test scripts

**What's Needed**:
- ⏭️ React UI for form builder interface
- ⏭️ GitHub token configuration (5 minutes)
- ⏭️ User acceptance testing

---

## 🚀 Quick Start for Frontend Developers

### 1. Get Access Token

```bash
# Use existing auth API to get token
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

# Save the access token
export TOKEN="eyJhbGc..."
```

### 2. Test API Connection

```bash
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"

# List templates
curl "$API_URL/form-builder/templates" -H "Authorization: Bearer $TOKEN"

# Query questions
curl "$API_URL/form-builder/questions?opportunity_subtype=SASE&page_size=5" -H "Authorization: Bearer $TOKEN"
```

### 3. Read Documentation

**Essential Reading** (in order):
1. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - One-page API overview (15 min)
2. [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) - Complete integration guide (45 min)
3. [API_SPEC.md](./API_SPEC.md) - Detailed API reference (as needed)

**Optional Reading**:
- [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) - GitHub setup (if deploying forms)
- [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md) - Known limitations
- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - Backend deployment info

---

## 📡 API Overview

### Base URL
```
https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
```

### Authentication
All requests require JWT token in header:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

### Endpoints Summary

| Endpoint | Method | Purpose | Permission |
|----------|--------|---------|------------|
| `/form-builder/templates` | GET | List templates | view |
| `/form-builder/templates` | POST | Create template | edit |
| `/form-builder/templates/:id` | GET | Get template | view |
| `/form-builder/templates/:id` | PUT | Update template | edit |
| `/form-builder/templates/:id` | DELETE | Delete template | admin |
| `/form-builder/templates/:id/deploy` | POST | Deploy to GitHub | edit |
| `/form-builder/questions` | GET | Query questions | view |
| `/form-builder/questions/:id` | GET | Get question | view |
| `/form-builder/preview` | POST | Generate HTML | view |

---

## 💻 Frontend Requirements

### Technology Stack (Recommended)

**Framework**:
- React 19 with TypeScript
- Vite for build tooling
- React Router for navigation

**UI Components**:
- Tailwind CSS for styling
- Shadcn/ui for components
- Lucide Icons

**Data Management**:
- TanStack Query (React Query) for server state
- Zustand or Context API for client state

**Drag & Drop**:
- @dnd-kit for question reordering

**Forms**:
- React Hook Form + Zod for validation

### Pages to Build

1. **Dashboard** (`/`) - Overview and recent templates
2. **Template List** (`/templates`) - Browse all templates
3. **Template Builder** (`/templates/new` & `/templates/:id`) - Create/edit templates
4. **Question Browser** (`/questions`) - Browse question database
5. **Settings** (`/settings`) - User preferences

### Core Features

**Must Have** (MVP):
- [ ] Template list with filters
- [ ] Template builder (two-panel layout)
- [ ] Question search and filtering
- [ ] Drag-and-drop question ordering
- [ ] Preview form before deployment
- [ ] Deploy to GitHub Pages

**Nice to Have** (Phase 2):
- [ ] Template duplication
- [ ] Bulk question import
- [ ] Template versioning
- [ ] Form analytics dashboard
- [ ] Question usage statistics

---

## 🔧 Integration Examples

### Example 1: Fetch and Display Templates

```typescript
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api'

const fetchTemplates = async () => {
  const token = localStorage.getItem('access_token')
  const response = await axios.get(`${API_URL}/form-builder/templates`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data.data
}

function TemplateList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['templates'],
    queryFn: fetchTemplates
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading templates</div>

  return (
    <div className="grid grid-cols-3 gap-4">
      {data.items.map(template => (
        <TemplateCard key={template.template_id} template={template} />
      ))}
    </div>
  )
}
```

### Example 2: Create New Template

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'

const createTemplate = async (templateData) => {
  const token = localStorage.getItem('access_token')
  const response = await axios.post(
    `${API_URL}/form-builder/templates`,
    templateData,
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return response.data.data
}

function useCreateTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template created successfully!')
    },
    onError: (error) => {
      toast.error('Failed to create template')
    }
  })
}

// Usage in component
function TemplateBuilder() {
  const createMutation = useCreateTemplate()

  const handleSave = () => {
    createMutation.mutate({
      template_name: "SASE Assessment",
      opportunity_type: "Security",
      opportunity_subtype: "SASE",
      questions: [
        { question_id: "q-001", weight: 10, is_required: true, sort_order: 1 }
      ]
    })
  }

  return <button onClick={handleSave}>Save Template</button>
}
```

### Example 3: Deploy to GitHub

```typescript
const deployTemplate = async (templateId: string, commitMessage?: string) => {
  const token = localStorage.getItem('access_token')
  const response = await axios.post(
    `${API_URL}/form-builder/templates/${templateId}/deploy`,
    { commit_message: commitMessage },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return response.data.data
}

function DeployButton({ templateId }: { templateId: string }) {
  const [isDeploying, setIsDeploying] = useState(false)
  const [deployedUrl, setDeployedUrl] = useState<string | null>(null)

  const handleDeploy = async () => {
    setIsDeploying(true)
    try {
      const result = await deployTemplate(templateId, "Deploy from UI")
      setDeployedUrl(result.deployed_url)
      toast.success('Form deployed successfully!')
    } catch (error) {
      if (error.response?.data?.error?.code === 'CONFIGURATION_ERROR') {
        toast.error('GitHub deployment not configured')
      } else {
        toast.error('Deployment failed')
      }
    } finally {
      setIsDeploying(false)
    }
  }

  return (
    <div>
      <button onClick={handleDeploy} disabled={isDeploying}>
        {isDeploying ? 'Deploying...' : 'Deploy to GitHub Pages'}
      </button>
      {deployedUrl && (
        <a href={deployedUrl} target="_blank" className="text-blue-600">
          View Deployed Form →
        </a>
      )}
    </div>
  )
}
```

---

## 📋 Data Models

### Template

```typescript
interface Template {
  template_id: string              // UUID
  template_name: string            // "SASE Assessment Survey"
  opportunity_type: string         // "Security"
  opportunity_subtype: string      // "SASE"
  status: 'draft' | 'published' | 'archived' | 'deleted'
  description?: string
  question_count?: number
  created_by: string               // User ID
  created_by_email?: string
  created_at: string               // ISO 8601 timestamp
  updated_at?: string
  deployed_url?: string            // GitHub Pages URL
  deployed_at?: string
  version?: number
  questions?: TemplateQuestion[]   // Included in GET /templates/:id
}
```

### Template Question

```typescript
interface TemplateQuestion {
  question_id: string              // UUID
  question_text: string
  category: string
  opportunity_type: string
  opportunity_subtype: string
  input_type: 'text' | 'textarea' | 'number' | 'radio' | 'select' | 'checkbox'
  help_text?: string
  weight: number | null            // null = "Info" question
  is_required: boolean
  sort_order: number
}
```

### Question

```typescript
interface Question {
  question_id: string
  question_text: string
  category: string
  opportunity_type: string
  opportunity_subtype: string
  input_type: 'text' | 'textarea' | 'number' | 'radio' | 'select' | 'checkbox'
  default_weight: number | null    // null = "Info" question
  help_text?: string
  is_active: boolean
  usage_count?: number             // Number of templates using this question
  templates?: string[]             // Template IDs using this question
  is_selected?: boolean            // True if in current template (when using template_id filter)
  selected_weight?: number | null
  selected_required?: boolean
}
```

### API Response

```typescript
interface APIResponse<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code: string
    details?: any
  }
  message?: string
  timestamp: string
}

interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total_count: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}
```

---

## 🎨 UI/UX Specifications

### Template Builder Layout

**Two-Panel Design**:

```
┌─────────────────────────────────────────────────────┐
│  Template Builder: SASE Assessment         [Save]   │
├───────────────────────┬─────────────────────────────┤
│  QUESTION BROWSER     │  TEMPLATE EDITOR            │
│  (Left Panel - 40%)   │  (Right Panel - 60%)        │
├───────────────────────┼─────────────────────────────┤
│  Search: [______]     │  Name: [____________]       │
│  Type: [Security ▼]   │  Type: [Security ▼]         │
│  Subtype: [SASE ▼]    │  Subtype: [SASE ▼]         │
│                       │  Description: [_________]   │
│  ┌─────────────────┐ │                             │
│  │ Do you have     │ │  SELECTED QUESTIONS (3)     │
│  │ firewall?       │ │                             │
│  │ ◉ Radio         │ │  1. ≡ Do you have firewall? │
│  │ Weight: 10      │ │     Weight: [10] ☑ Required │
│  │   [+ Add]       │ │     [Remove]                │
│  └─────────────────┘ │                             │
│                       │  2. ≡ Network topology      │
│  [Load More]          │     Weight: [Info] ☐ Req.  │
│                       │     [Remove]                │
│                       │                             │
│                       │  [Preview] [Deploy]         │
└───────────────────────┴─────────────────────────────┘
```

### Color Scheme

**Status Colors**:
- Draft: Gray (#6B7280)
- Published: Green (#10B981)
- Archived: Red (#EF4444)

**UI Elements**:
- Primary: Blue (#3B82F6)
- Secondary: Purple (#8B5CF6)
- Danger: Red (#EF4444)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)

### Component Library

Use **Shadcn/ui** components:
- Button
- Card
- Dialog (for modals)
- Input
- Select
- Textarea
- Badge (for status)
- Alert (for errors)
- Skeleton (for loading states)

---

## ⚠️ Important Considerations

### 1. BigQuery Streaming Buffer Limitation

**Issue**: Templates cannot be updated or deleted within 90 minutes of creation

**Frontend Impact**:
- Show warning when trying to update/delete new templates
- Display countdown timer: "Can update in 87 minutes"
- Alternatively, disable Update/Delete buttons with tooltip

**Example Error Handling**:
```typescript
if (error.response?.data?.error?.details?.error?.includes('streaming buffer')) {
  toast.error('Cannot update template within 90 minutes of creation. Please try again later.')
  // Optionally show countdown timer
}
```

### 2. GitHub Configuration

**Issue**: Deployment requires GitHub token in backend

**Frontend Impact**:
- Check if deployment is available before showing Deploy button
- Show setup instructions if not configured
- Handle 503 Service Unavailable error gracefully

**Example Check**:
```typescript
const checkDeploymentAvailable = async () => {
  try {
    await deployTemplate(templateId)
    return true
  } catch (error) {
    if (error.response?.data?.error?.code === 'CONFIGURATION_ERROR') {
      return false
    }
    throw error
  }
}
```

### 3. "Info" Weight Handling

**Special Case**: Questions can have weight = "Info" (stored as NULL)

**Frontend Impact**:
- Show "Info" badge for null weights
- Allow users to select "Info" instead of numeric weight
- Use select with options: [1-100, "Info"]

**Example Component**:
```tsx
<select value={weight} onChange={handleWeightChange}>
  <option value="Info">Info (no scoring)</option>
  {[...Array(100)].map((_, i) => (
    <option key={i + 1} value={i + 1}>{i + 1}</option>
  ))}
</select>
```

### 4. Authentication Flow

**Token Management**:
- Store access token in localStorage
- Include in all API requests
- Handle 401 errors (redirect to login)
- Refresh token when expired

**Example Axios Interceptor**:
```typescript
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

---

## 🧪 Testing Recommendations

### Unit Tests
- Component rendering
- User interactions (clicks, typing)
- State management
- Form validation

### Integration Tests
- Template creation flow
- Question selection flow
- Drag-and-drop reordering
- Preview generation
- Deployment flow

### E2E Tests (Cypress/Playwright)
- Complete template creation workflow
- Search and filter questions
- Deploy template to GitHub
- Error handling scenarios

### Example Test
```typescript
describe('Template Builder', () => {
  it('should create a new template', async () => {
    render(<TemplateBuilder />)

    // Fill in template metadata
    fireEvent.change(screen.getByLabelText('Template Name'), {
      target: { value: 'Test Template' }
    })

    // Select questions
    const question = screen.getByText('Do you have firewall?')
    fireEvent.click(question.querySelector('[data-testid="add-button"]'))

    // Save template
    fireEvent.click(screen.getByText('Save Template'))

    await waitFor(() => {
      expect(screen.getByText('Template created successfully')).toBeInTheDocument()
    })
  })
})
```

---

## 📦 Deployment

### Frontend Hosting Options

1. **Firebase Hosting** (Recommended)
   - Fast CDN
   - Easy SSL
   - Custom domains
   - GitHub Actions integration

2. **Google Cloud Storage + Load Balancer**
   - Static site hosting
   - Global CDN
   - Integrated with GCP project

3. **Vercel/Netlify**
   - Automatic deployments
   - Preview URLs for PRs
   - Easy DNS management

### Build Configuration

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:e2e": "cypress run"
  }
}
```

### Environment Variables

```env
# .env.production
VITE_API_BASE_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
VITE_AUTH_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
```

---

## 🔍 Quality Checklist

### Before Development
- [ ] Read QUICK_REFERENCE.md
- [ ] Read FRONTEND_INTEGRATION.md
- [ ] Test API with curl/Postman
- [ ] Understand data models
- [ ] Review UI mockups

### During Development
- [ ] Use TypeScript for type safety
- [ ] Implement error boundaries
- [ ] Add loading states
- [ ] Handle empty states
- [ ] Add proper error messages
- [ ] Test with real API
- [ ] Optimize performance (memoization, lazy loading)

### Before Production
- [ ] All core features working
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Cross-browser testing
- [ ] Performance testing (Lighthouse score > 90)
- [ ] Security audit (XSS, CSRF protection)
- [ ] User acceptance testing

---

## 📞 Support & Resources

### Documentation
- **Quick Reference**: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- **API Spec**: [API_SPEC.md](./API_SPEC.md)
- **Integration Guide**: [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)
- **GitHub Setup**: [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md)

### Testing
- **Test Script**: `./test_api.sh` (run comprehensive API tests)
- **Example Script**: `./deploy_example.sh` (see complete workflow)

### API Endpoints
- **Base URL**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- **Auth API**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api

### Getting Help
1. Check documentation first
2. Review error messages in API responses
3. Check Cloud Function logs:
   ```bash
   gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50
   ```
4. Contact backend team with:
   - Request details (endpoint, method, body)
   - Response received
   - Expected behavior
   - Steps to reproduce

---

## 🎯 Success Criteria

### MVP (Minimum Viable Product)
- [ ] Users can browse templates
- [ ] Users can create new templates
- [ ] Users can search and add questions
- [ ] Users can reorder questions (drag-and-drop)
- [ ] Users can preview forms
- [ ] Users can deploy to GitHub Pages
- [ ] Error messages are clear and helpful
- [ ] Loading states are shown during API calls

### Phase 2 Enhancements
- [ ] Template duplication
- [ ] Advanced filtering
- [ ] Bulk operations
- [ ] Form analytics
- [ ] Question usage statistics
- [ ] Template versioning
- [ ] Collaborative editing

---

## 📅 Timeline Estimate

### Sprint 1 (Week 1) - Foundation
- [ ] Project setup (React + Vite + TypeScript)
- [ ] Install dependencies
- [ ] API client configuration
- [ ] Authentication integration
- [ ] Basic routing

### Sprint 2 (Week 2) - Core Pages
- [ ] Template list page
- [ ] Question browser page
- [ ] Basic layout and navigation

### Sprint 3 (Week 3) - Template Builder
- [ ] Template builder layout (two panels)
- [ ] Question search and filtering
- [ ] Question selection
- [ ] Drag-and-drop reordering

### Sprint 4 (Week 4) - Features
- [ ] Form preview
- [ ] GitHub deployment
- [ ] Error handling
- [ ] Loading states

### Sprint 5 (Week 5) - Polish
- [ ] Responsive design
- [ ] Accessibility
- [ ] Testing
- [ ] Bug fixes

### Sprint 6 (Week 6) - Deployment
- [ ] Production build
- [ ] Deploy to hosting
- [ ] User acceptance testing
- [ ] Documentation

**Total Estimate**: 6 weeks for MVP

---

## 🚦 Getting Started (First Steps)

### Day 1: Setup & Exploration
1. **Read documentation** (2 hours)
   - QUICK_REFERENCE.md
   - FRONTEND_INTEGRATION.md

2. **Test API** (1 hour)
   - Get auth token
   - Test endpoints with curl
   - Understand response formats

3. **Setup project** (2 hours)
   - Create React + Vite + TypeScript project
   - Install dependencies
   - Configure Tailwind CSS

### Day 2: API Integration
1. **Create API client** (2 hours)
   - Axios setup
   - Request/response interceptors
   - TypeScript types

2. **Test authentication** (2 hours)
   - Integrate with auth API
   - Token storage
   - Protected routes

3. **Create first API call** (2 hours)
   - Fetch templates
   - Display in UI
   - Handle loading/error states

### Day 3-5: Build First Page
1. **Template List Page**
   - Table/Grid layout
   - Filters and search
   - Pagination
   - Actions (Edit, Deploy, Delete)

### Week 2+: Continue with other pages...

---

## ✅ Handoff Checklist

### Backend Team
- [x] API implementation complete
- [x] All endpoints tested
- [x] Documentation written
- [x] Examples provided
- [x] Deployed to Cloud Functions
- [x] Access credentials shared

### Frontend Team (To Confirm)
- [ ] Documentation reviewed
- [ ] API access verified
- [ ] Development environment setup
- [ ] First API call successful
- [ ] Questions addressed
- [ ] Timeline agreed upon

---

**Last Updated**: November 6, 2025
**Backend Version**: 1.1.0
**Contact**: Backend Team via Slack/Email

**Ready to Build! 🚀**
