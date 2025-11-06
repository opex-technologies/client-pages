# Form Builder UI

**Version**: 1.0.0
**Created**: November 6, 2025
**Status**: In Development

React-based web application for creating and managing survey forms for Opex Technologies.

## Features

- Create and manage form templates
- Browse and select questions from database (1,041 questions)
- Drag-and-drop question selection
- Real-time form preview
- Deploy forms to GitHub Pages
- JWT authentication with RBAC permissions

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **React Hook Form** - Form handling
- **React Hot Toast** - Notifications
- **Lucide React** - Icons
- **@dnd-kit** - Drag and drop
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 20.16.0+
- npm 10+

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`.

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
VITE_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
VITE_AUTH_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
VITE_ENV=development
```

## Project Structure

```
src/
├── pages/           # Page components
├── components/      # Reusable components
├── services/        # API clients
├── hooks/           # Custom React hooks
├── utils/           # Utility functions
├── contexts/        # React contexts
├── store/           # Zustand stores
├── config.js        # Configuration
└── main.jsx         # Application entry point
```

## Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## API Integration

The Form Builder connects to two APIs:

- **Form Builder API**: Template and question management
- **Auth API**: Authentication and permissions

See the backend documentation for API details:
- [Form Builder API](../../backend/form_builder/README.md)
- [Auth API](../../backend/auth/README.md)

## Authentication

The application uses JWT authentication with role-based access control (RBAC):

- **View**: Can list and view templates, query questions
- **Edit**: Can create and update templates
- **Admin**: Can delete templates and manage questions

## Deployment

The Form Builder UI can be deployed to:

- **GitHub Pages** (recommended)
- **Netlify**
- **Vercel**
- **Cloud Storage** (static hosting)

```bash
# Build for production
npm run build

# Deploy to GitHub Pages (example)
npm run build && gh-pages -d dist
```

## Features Roadmap

### Phase 1 (Current)
- [x] Project setup with Vite and Tailwind
- [ ] API client implementation
- [ ] Layout and navigation
- [ ] Dashboard page
- [ ] Template list page
- [ ] Template card component

### Phase 2
- [ ] Template editor
- [ ] Question browser
- [ ] Drag-and-drop question selection
- [ ] Form preview
- [ ] Save draft functionality

### Phase 3
- [ ] GitHub deployment integration
- [ ] Deployment history
- [ ] Analytics dashboard
- [ ] Advanced filtering

## Documentation

- [Getting Started](../../backend/form_builder/GETTING_STARTED.md)
- [Frontend Integration Guide](../../backend/form_builder/FRONTEND_INTEGRATION.md)
- [Frontend Handoff](../../backend/form_builder/HANDOFF.md)
- [API Reference](../../backend/form_builder/API_SPEC.md)

## Support

For questions or issues, refer to the backend documentation or contact the development team.

---

**Last Updated**: November 6, 2025
**Maintainer**: Dayta Analytics - Frontend Team
