# Form Builder - Frontend Integration Guide

**For**: React Form Builder UI
**API Version**: 1.1.0
**Created**: November 6, 2025

## Overview

This guide provides specifications for building the React frontend that integrates with the Form Builder API. The frontend will enable users to create, manage, and deploy custom survey forms through an intuitive drag-and-drop interface.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                React Frontend                     │
│  (Vite + React 19 + Tailwind CSS + Shadcn/ui)   │
└───────────────────┬──────────────────────────────┘
                    │
                    │ HTTP + JWT
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐   ┌─────────────┐   ┌────────────┐
│  Auth  │   │ Form Builder│   │   GitHub   │
│  API   │   │     API     │   │   Pages    │
└────────┘   └─────────────┘   └────────────┘
```

---

## Tech Stack Recommendations

### Core Framework
- **React 19** - Latest React with improved performance
- **Vite** - Fast build tool and dev server
- **TypeScript** - Type safety and better DX

### UI Components
- **Tailwind CSS** - Utility-first styling
- **Shadcn/ui** - High-quality React components
- **Lucide Icons** - Modern icon library

### State Management
- **TanStack Query (React Query)** - Server state management
- **Zustand** or **Context API** - Client state

### Drag & Drop
- **@dnd-kit** - Modern drag-and-drop toolkit
- **react-beautiful-dnd** - Alternative option

### Form Handling
- **React Hook Form** - Performant form library
- **Zod** - Schema validation

### Other Libraries
- **Axios** - HTTP client
- **date-fns** - Date utilities
- **React Router** - Navigation

---

## Pages & Routes

### Main Application Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Overview and recent templates |
| `/templates` | TemplateList | List all templates |
| `/templates/new` | TemplateBuilder | Create new template |
| `/templates/:id` | TemplateBuilder | Edit existing template |
| `/templates/:id/preview` | TemplatePreview | Preview form HTML |
| `/questions` | QuestionBrowser | Browse question database |
| `/settings` | Settings | User settings |

---

## Core Features

### 1. Template List Page

**Purpose**: View and manage all form templates

**Features**:
- Table/Grid view of templates
- Filters: opportunity_type, opportunity_subtype, status, created_by
- Search functionality
- Sort by: name, created_at, updated_at
- Pagination
- Actions: Edit, Preview, Deploy, Delete
- Status badges: Draft, Published, Archived

**API Calls**:
```typescript
// Get templates with filters
GET /form-builder/templates?opportunity_type=Security&status=published&page=1&page_size=20

// Delete template
DELETE /form-builder/templates/:id
```

**UI Mock**:
```
┌─────────────────────────────────────────────────────┐
│ Form Templates                    [+ New Template]  │
├─────────────────────────────────────────────────────┤
│ Filters: [Type ▼] [Subtype ▼] [Status ▼]  Search:□ │
├─────────────────────────────────────────────────────┤
│ Name             │ Type    │ Status  │ Questions   │
│ SASE Assessment  │ Security│ Draft   │ 67    [Edit]│
│ UCaaS Survey     │ Network │Published│ 98  [Deploy]│
└─────────────────────────────────────────────────────┘
```

---

### 2. Template Builder Page

**Purpose**: Create and edit form templates

**Layout**: Two-panel design

#### Left Panel: Question Browser
- Search questions by keyword
- Filter by: opportunity_type, opportunity_subtype, category
- Display question cards with:
  - Question text
  - Input type
  - Default weight
  - Category/Type badges
  - "Info" indicator if default_weight is null
- Pagination
- "Add to Template" button on each card

#### Right Panel: Template Editor
- **Template Metadata** (top section):
  - Template Name (text input)
  - Opportunity Type (select)
  - Opportunity Subtype (select)
  - Description (textarea)
  - Status badge

- **Selected Questions** (middle section):
  - Drag-and-drop sortable list
  - Each question card shows:
    - Sort order number
    - Question text (truncated)
    - Weight input (number or "Info")
    - Required checkbox
    - Remove button
    - Drag handle

- **Actions** (bottom section):
  - Save Draft
  - Preview Form
  - Deploy to GitHub Pages
  - Cancel

**UI Mock**:
```
┌─────────────────────────────────────────────────────────────┐
│  Create Template: SASE Assessment                          │
├──────────────────────┬──────────────────────────────────────┤
│ QUESTION BROWSER     │ TEMPLATE EDITOR                      │
├──────────────────────┼──────────────────────────────────────┤
│ Search: [firewall  ]│ Name: [SASE Assessment            ]  │
│ Type: [Security ▼]  │ Type: [Security ▼] Sub: [SASE ▼]    │
│                      │ Desc: [Comprehensive assessment...]  │
│ ┌─────────────────┐ │                                       │
│ │ Do you have     │ │ SELECTED QUESTIONS (3)                │
│ │ firewall?       │ │ ┌─────────────────────────────────┐  │
│ │ Type: Radio     │ │ │ 1 ≡ Do you have firewall?       │  │
│ │ Weight: 10      │ │ │    Weight: [10] ☑ Required  [×] │  │
│ │    [+ Add]      │ │ └─────────────────────────────────┘  │
│ └─────────────────┘ │ ┌─────────────────────────────────┐  │
│                      │ │ 2 ≡ Describe network setup      │  │
│ [Load More]          │ │    Weight: [Info] ☐ Required [×]│  │
│                      │ └─────────────────────────────────┘  │
│                      │                                       │
│                      │ [Save Draft] [Preview] [Deploy]      │
└──────────────────────┴──────────────────────────────────────┘
```

**API Calls**:
```typescript
// Load questions
GET /form-builder/questions?opportunity_subtype=SASE&search=firewall&page=1

// Get existing template (edit mode)
GET /form-builder/templates/:id

// Create template
POST /form-builder/templates
Body: { template_name, opportunity_type, opportunity_subtype, description, questions }

// Update template
PUT /form-builder/templates/:id
Body: { template_name, questions, ... }

// Preview
POST /form-builder/preview
Body: { template_id }

// Deploy
POST /form-builder/templates/:id/deploy
Body: { commit_message }
```

**State Management**:
```typescript
interface TemplateEditorState {
  template_name: string
  opportunity_type: string
  opportunity_subtype: string
  description: string
  selectedQuestions: SelectedQuestion[]
  isDirty: boolean
  isSaving: boolean
}

interface SelectedQuestion {
  question_id: string
  question_text: string
  input_type: string
  weight: number | 'Info'
  is_required: boolean
  sort_order: number
}
```

---

### 3. Question Browser Page

**Purpose**: Browse and search the complete question database

**Features**:
- Advanced filtering
- Full-text search
- Question statistics (usage count, templates using it)
- View which templates use each question
- Responsive card/table view

**API Calls**:
```typescript
// Query questions with filters
GET /form-builder/questions?category=Security&search=compliance&page=1&page_size=50

// Get question details with usage stats
GET /form-builder/questions/:id
```

---

### 4. Preview Modal/Page

**Purpose**: Display generated HTML form before deployment

**Features**:
- Full-screen modal or dedicated page
- Live form preview (iframe or rendered HTML)
- Download HTML button
- Deploy button (if not already deployed)
- Close/Back button

**API Calls**:
```typescript
// Generate preview
POST /form-builder/preview
Body: { template_id }

// Response contains HTML string
```

**Implementation**:
```typescript
const PreviewModal = () => {
  const [html, setHtml] = useState('')

  useEffect(() => {
    generatePreview(templateId).then(response => {
      setHtml(response.data.html)
    })
  }, [templateId])

  return (
    <div className="modal">
      <iframe srcDoc={html} className="w-full h-full" />
      <button onClick={downloadHtml}>Download HTML</button>
      <button onClick={deployForm}>Deploy to GitHub</button>
    </div>
  )
}
```

---

### 5. Deploy Flow

**Purpose**: Deploy form to GitHub Pages

**Flow**:
1. User clicks "Deploy" button
2. Show modal with:
   - Commit message input (optional)
   - Preview of deployment URL
   - Deploy button
3. Call deploy API
4. Show success with:
   - Public URL (clickable link)
   - Commit SHA
   - Copy URL button
   - Visit URL button
5. Update template status to "Published"

**API Call**:
```typescript
POST /form-builder/templates/:id/deploy
Body: { commit_message: "Deploy SASE assessment v2" }

Response:
{
  "deployed_url": "https://opextech.github.io/forms/forms/sase_assessment.html",
  "commit_sha": "abc123...",
  "file_path": "forms/sase_assessment.html"
}
```

**Error Handling**:
- If GitHub not configured: Show setup instructions link
- If deployment fails: Show error with retry button
- If BigQuery metadata update delayed: Show warning but indicate deployment succeeded

---

## API Integration Layer

### API Client Setup

```typescript
// api/client.ts
import axios from 'axios'

const API_BASE_URL = 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
    }
    return Promise.reject(error)
  }
)
```

### API Service Functions

```typescript
// api/formBuilder.ts
import { apiClient } from './client'

export interface Template {
  template_id: string
  template_name: string
  opportunity_type: string
  opportunity_subtype: string
  status: 'draft' | 'published' | 'archived'
  description?: string
  question_count?: number
  created_at: string
  deployed_url?: string
}

export interface Question {
  question_id: string
  question_text: string
  category: string
  opportunity_type: string
  opportunity_subtype: string
  input_type: string
  default_weight: number | null
  help_text?: string
  is_selected?: boolean
  selected_weight?: number | null
  selected_required?: boolean
}

export const formBuilderAPI = {
  // Templates
  getTemplates: (params?: {
    opportunity_type?: string
    opportunity_subtype?: string
    status?: string
    page?: number
    page_size?: number
  }) => apiClient.get('/form-builder/templates', { params }),

  getTemplate: (id: string) =>
    apiClient.get(`/form-builder/templates/${id}`),

  createTemplate: (data: {
    template_name: string
    opportunity_type: string
    opportunity_subtype: string
    description?: string
    questions: Array<{
      question_id: string
      weight: number | 'Info'
      is_required: boolean
      sort_order: number
    }>
  }) => apiClient.post('/form-builder/templates', data),

  updateTemplate: (id: string, data: Partial<Template>) =>
    apiClient.put(`/form-builder/templates/${id}`, data),

  deleteTemplate: (id: string) =>
    apiClient.delete(`/form-builder/templates/${id}`),

  deployTemplate: (id: string, commit_message?: string) =>
    apiClient.post(`/form-builder/templates/${id}/deploy`, { commit_message }),

  // Questions
  getQuestions: (params?: {
    category?: string
    opportunity_type?: string
    opportunity_subtype?: string
    search?: string
    template_id?: string
    page?: number
    page_size?: number
  }) => apiClient.get('/form-builder/questions', { params }),

  getQuestion: (id: string) =>
    apiClient.get(`/form-builder/questions/${id}`),

  // Preview
  generatePreview: (template_id: string) =>
    apiClient.post('/form-builder/preview', { template_id })
}
```

### React Query Hooks

```typescript
// hooks/useFormBuilder.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formBuilderAPI } from '../api/formBuilder'

export const useTemplates = (filters = {}) => {
  return useQuery({
    queryKey: ['templates', filters],
    queryFn: () => formBuilderAPI.getTemplates(filters)
  })
}

export const useTemplate = (id: string) => {
  return useQuery({
    queryKey: ['template', id],
    queryFn: () => formBuilderAPI.getTemplate(id),
    enabled: !!id
  })
}

export const useCreateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: formBuilderAPI.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
}

export const useDeployTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, commit_message }: { id: string, commit_message?: string }) =>
      formBuilderAPI.deployTemplate(id, commit_message),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['template', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    }
  })
}

export const useQuestions = (filters = {}) => {
  return useQuery({
    queryKey: ['questions', filters],
    queryFn: () => formBuilderAPI.getQuestions(filters)
  })
}
```

---

## Component Examples

### Template Card Component

```tsx
// components/TemplateCard.tsx
interface TemplateCardProps {
  template: Template
  onEdit: (id: string) => void
  onDeploy: (id: string) => void
  onDelete: (id: string) => void
}

export const TemplateCard = ({ template, onEdit, onDeploy, onDelete }: TemplateCardProps) => {
  const statusColor = {
    draft: 'bg-gray-100 text-gray-800',
    published: 'bg-green-100 text-green-800',
    archived: 'bg-red-100 text-red-800'
  }

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold">{template.template_name}</h3>
        <span className={`px-2 py-1 rounded text-xs ${statusColor[template.status]}`}>
          {template.status}
        </span>
      </div>

      <div className="text-sm text-gray-600 mb-3">
        <p>{template.opportunity_type} › {template.opportunity_subtype}</p>
        <p>{template.question_count} questions</p>
        {template.deployed_url && (
          <a href={template.deployed_url} target="_blank" className="text-blue-600 hover:underline">
            View Public Form
          </a>
        )}
      </div>

      <div className="flex gap-2">
        <button onClick={() => onEdit(template.template_id)} className="btn-primary">
          Edit
        </button>
        <button onClick={() => onDeploy(template.template_id)} className="btn-secondary">
          Deploy
        </button>
        <button onClick={() => onDelete(template.template_id)} className="btn-danger">
          Delete
        </button>
      </div>
    </div>
  )
}
```

### Question Card Component

```tsx
// components/QuestionCard.tsx
interface QuestionCardProps {
  question: Question
  onAdd?: (question: Question) => void
  isSelected?: boolean
}

export const QuestionCard = ({ question, onAdd, isSelected }: QuestionCardProps) => {
  const inputTypeIcon = {
    radio: '◉',
    text: '▭',
    textarea: '▬',
    number: '№',
    select: '▼',
    checkbox: '☐'
  }

  const isInfo = question.default_weight === null

  return (
    <div className={`border rounded p-3 ${isSelected ? 'bg-blue-50 border-blue-500' : ''}`}>
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs bg-gray-200 px-2 py-1 rounded">
          {inputTypeIcon[question.input_type]} {question.input_type}
        </span>
        {isInfo && (
          <span className="text-xs bg-yellow-100 px-2 py-1 rounded">Info</span>
        )}
      </div>

      <p className="text-sm mb-2">{question.question_text}</p>

      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>{question.category}</span>
        <span>Weight: {question.default_weight ?? 'Info'}</span>
      </div>

      {onAdd && !isSelected && (
        <button
          onClick={() => onAdd(question)}
          className="mt-2 w-full btn-primary text-sm"
        >
          + Add to Template
        </button>
      )}
    </div>
  )
}
```

---

## State Management

### Template Builder State (Zustand)

```typescript
// store/templateBuilder.ts
import create from 'zustand'

interface SelectedQuestion {
  question_id: string
  question_text: string
  input_type: string
  weight: number | 'Info'
  is_required: boolean
  sort_order: number
}

interface TemplateBuilderStore {
  template_name: string
  opportunity_type: string
  opportunity_subtype: string
  description: string
  selectedQuestions: SelectedQuestion[]
  isDirty: boolean

  setTemplateName: (name: string) => void
  setOpportunityType: (type: string) => void
  setOpportunitySubtype: (subtype: string) => void
  setDescription: (desc: string) => void
  addQuestion: (question: Question) => void
  removeQuestion: (question_id: string) => void
  updateQuestion: (question_id: string, updates: Partial<SelectedQuestion>) => void
  reorderQuestions: (startIndex: number, endIndex: number) => void
  resetTemplate: () => void
  loadTemplate: (template: Template) => void
}

export const useTemplateBuilder = create<TemplateBuilderStore>((set) => ({
  template_name: '',
  opportunity_type: '',
  opportunity_subtype: '',
  description: '',
  selectedQuestions: [],
  isDirty: false,

  setTemplateName: (name) => set({ template_name: name, isDirty: true }),
  setOpportunityType: (type) => set({ opportunity_type: type, isDirty: true }),
  setOpportunitySubtype: (subtype) => set({ opportunity_subtype: subtype, isDirty: true }),
  setDescription: (desc) => set({ description: desc, isDirty: true }),

  addQuestion: (question) => set((state) => ({
    selectedQuestions: [
      ...state.selectedQuestions,
      {
        question_id: question.question_id,
        question_text: question.question_text,
        input_type: question.input_type,
        weight: question.default_weight ?? 'Info',
        is_required: true,
        sort_order: state.selectedQuestions.length + 1
      }
    ],
    isDirty: true
  })),

  removeQuestion: (question_id) => set((state) => ({
    selectedQuestions: state.selectedQuestions
      .filter(q => q.question_id !== question_id)
      .map((q, idx) => ({ ...q, sort_order: idx + 1 })),
    isDirty: true
  })),

  updateQuestion: (question_id, updates) => set((state) => ({
    selectedQuestions: state.selectedQuestions.map(q =>
      q.question_id === question_id ? { ...q, ...updates } : q
    ),
    isDirty: true
  })),

  reorderQuestions: (startIndex, endIndex) => set((state) => {
    const result = Array.from(state.selectedQuestions)
    const [removed] = result.splice(startIndex, 1)
    result.splice(endIndex, 0, removed)

    return {
      selectedQuestions: result.map((q, idx) => ({ ...q, sort_order: idx + 1 })),
      isDirty: true
    }
  }),

  resetTemplate: () => set({
    template_name: '',
    opportunity_type: '',
    opportunity_subtype: '',
    description: '',
    selectedQuestions: [],
    isDirty: false
  }),

  loadTemplate: (template) => set({
    template_name: template.template_name,
    opportunity_type: template.opportunity_type,
    opportunity_subtype: template.opportunity_subtype,
    description: template.description || '',
    selectedQuestions: template.questions || [],
    isDirty: false
  })
}))
```

---

## Error Handling

### Common Errors & User Messages

| Error Code | User Message | Action |
|------------|--------------|--------|
| 401 | "Your session has expired. Please log in again." | Redirect to login |
| 403 | "You don't have permission to perform this action." | Show contact admin message |
| 404 | "Template not found. It may have been deleted." | Redirect to template list |
| 500 (BigQuery) | "Cannot update template within 90 minutes of creation. Please try again later." | Show retry button with timer |
| 503 (GitHub) | "GitHub deployment is not configured. Contact your administrator." | Show setup instructions link |

### Error Boundary Component

```typescript
// components/ErrorBoundary.tsx
export const ErrorBoundary = ({ children }) => {
  const [hasError, setHasError] = useState(false)

  if (hasError) {
    return (
      <div className="error-container">
        <h2>Something went wrong</h2>
        <button onClick={() => setHasError(false)}>Try again</button>
      </div>
    )
  }

  return children
}
```

---

## Testing Requirements

### Unit Tests
- Component rendering
- User interactions
- State management
- API client functions

### Integration Tests
- Complete template creation flow
- Question selection and reordering
- Form preview generation
- Deployment flow

### E2E Tests
- Create template end-to-end
- Deploy template to GitHub
- Error scenarios

---

## Performance Considerations

### Optimizations
- **Lazy Loading**: Load components on demand
- **Pagination**: Limit question/template lists to 50 items
- **Debounce Search**: Wait 300ms before searching
- **Memoization**: Use React.memo for expensive components
- **Virtual Scrolling**: For long question lists (react-window)

### Caching Strategy
- Cache template list for 5 minutes
- Cache question database for 10 minutes
- Invalidate on mutations
- Optimistic updates for better UX

---

## Deployment

### Environment Variables

```env
# .env.production
VITE_API_BASE_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
VITE_AUTH_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
```

### Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net',
        changeOrigin: true
      }
    }
  }
})
```

---

## Next Steps

1. **Setup Project** - Initialize React + Vite + TypeScript
2. **Install Dependencies** - TanStack Query, Tailwind, Shadcn/ui, @dnd-kit
3. **Create API Client** - Axios setup with auth interceptors
4. **Build Template List** - First working page
5. **Build Question Browser** - Second page
6. **Build Template Builder** - Core feature
7. **Implement Drag & Drop** - Question reordering
8. **Add Preview** - HTML preview modal
9. **Add Deploy** - GitHub deployment flow
10. **Testing** - Unit and E2E tests
11. **Deploy** - Host on Firebase Hosting or Cloud Storage

---

**Documentation**:
- API Spec: [API_SPEC.md](./API_SPEC.md)
- Quick Reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- GitHub Setup: [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md)

**Last Updated**: November 6, 2025
**Version**: 1.0
