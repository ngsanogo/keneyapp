# KeneyApp Frontend

Modern React TypeScript frontend for the KeneyApp healthcare management platform.

## Technology Stack

- **React 18**: Modern React with hooks
- **TypeScript 4.9**: Type-safe JavaScript
- **React Router v6**: Client-side routing
- **Axios**: HTTP client for API requests
- **React Testing Library**: Component testing

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable React components
│   │   ├── Header.tsx     # Navigation header
│   │   ├── LoadingSpinner.tsx  # Loading states
│   │   ├── ErrorBoundary.tsx   # Error handling
│   │   └── NotificationToast.tsx  # Notifications
│   ├── contexts/          # React context providers
│   │   └── AuthContext.tsx  # Authentication context
│   ├── hooks/             # Custom React hooks
│   │   └── useApi.ts      # API call hook with error handling
│   ├── pages/             # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── PatientsPage.tsx
│   │   ├── AppointmentsPage.tsx
│   │   └── PrescriptionsPage.tsx
│   ├── App.tsx            # Main application component
│   ├── App.css            # Global styles
│   ├── index.tsx          # Application entry point
│   └── index.css          # Base styles
├── package.json           # Dependencies and scripts
└── tsconfig.json          # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on <http://localhost:8000>

### Installation

```bash
npm install
```

### Development

```bash
# Start development server
npm start

# Runs on http://localhost:3000
```

### Build

```bash
# Create production build
npm run build

# Output in build/ directory
```

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watchAll
```

### Linting & Formatting

```bash
# Run ESLint
npm run lint

# Format code with Prettier
npm run format

# Check formatting
npm run format:check
```

## Key Features

### Authentication

- JWT-based authentication
- Secure token storage
- Auto-logout on token expiration
- Role-based access control

### Components

#### LoadingSpinner

```typescript
import LoadingSpinner from './components/LoadingSpinner';

<LoadingSpinner
  size="medium"
  message="Loading patients..."
  fullScreen={false}
/>
```

#### ErrorBoundary

```typescript
import ErrorBoundary from './components/ErrorBoundary';

<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

#### NotificationToast

```typescript
import NotificationToast from './components/NotificationToast';

<NotificationToast
  message="Patient created successfully"
  type="success"
  duration={5000}
  onClose={() => console.log('Closed')}
/>
```

### Custom Hooks

#### useApi Hook

```typescript
import { useApi } from './hooks/useApi';

function PatientsPage() {
  const { data, loading, error, execute } = useApi<Patient[]>();

  useEffect(() => {
    execute({
      method: 'GET',
      url: '/api/v1/patients',
      headers: { Authorization: `Bearer ${token}` }
    });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div>Error: {error}</div>;

  return <div>{/* Render patients */}</div>;
}
```

### Authentication Context

The `AuthContext` provides authentication state and methods throughout the app:

```typescript
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { user, token, login, logout, isAuthenticated } = useAuth();

  // Access user info, token, and auth methods
}
```

## Environment Variables

Create `.env.local` for local development:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1
```

## API Integration

The frontend communicates with the backend API at:

- Default: `http://localhost:8000/api/v1`
- Production: Configure via environment variables

### Example API Calls

```typescript
// Login
const response = await axios.post('/api/v1/auth/login', {
  username: 'admin',
  password: 'admin123'
});

// Get patients (authenticated)
const patients = await axios.get('/api/v1/patients', {
  headers: { Authorization: `Bearer ${token}` }
});

// Create patient
const newPatient = await axios.post('/api/v1/patients', patientData, {
  headers: { Authorization: `Bearer ${token}` }
});
```

## Styling

- CSS Modules for component-specific styles
- Global styles in `index.css` and `App.css`
- Inline styles for dynamic/conditional styling
- Consider adding a CSS framework (Tailwind, Material-UI, etc.) for production

## Best Practices

### Component Design

- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use TypeScript interfaces for props

### State Management

- Use React Context for global state (auth, theme, etc.)
- Use local state for component-specific data
- Consider adding Redux/Zustand for complex state

### Error Handling

- Wrap routes with ErrorBoundary
- Use try-catch for async operations
- Show user-friendly error messages
- Log errors for debugging

### Performance

- Use React.memo for expensive components
- Implement code splitting with React.lazy
- Optimize images and assets
- Use production build for deployment

## Common Issues

### CORS Errors

If you encounter CORS errors, ensure the backend is configured to allow requests from `http://localhost:3000`.

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Module Not Found

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Scripts Reference

| Command | Description |
|---------|-------------|
| `npm start` | Start development server |
| `npm run build` | Create production build |
| `npm test` | Run test suite |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm run format:check` | Check code formatting |
| `npm run eject` | Eject from Create React App (irreversible) |

## Future Enhancements

- [ ] Add state management library (Redux/Zustand)
- [ ] Implement form validation library (Formik/React Hook Form)
- [ ] Add UI component library (Material-UI/Ant Design)
- [ ] Implement internationalization (i18n)
- [ ] Add end-to-end testing (Cypress/Playwright)
- [ ] Implement PWA features
- [ ] Add accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Implement real-time updates (WebSockets)

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Use meaningful commit messages
5. Keep components small and focused

## License

Proprietary - ISDATA Consulting

## Support

For questions or issues, contact: <contact@isdataconsulting.com>
