# Frontend Application

This directory contains the frontend React application for the Crypto Regulatory Compliance Checker.

## Directory Structure

```
frontend/
├── public/          # Static assets and index.html
├── src/             # Source code
│   ├── components/  # Reusable UI components
│   ├── pages/       # Page components and routes
│   ├── services/    # API client and service integrations
│   ├── hooks/       # Custom React hooks
│   ├── utils/       # Utility functions and helpers
│   ├── types/       # TypeScript type definitions
│   ├── styles/      # Global styles and theme
│   └── App.tsx      # Root application component
├── node_modules/    # Dependencies (gitignored)
└── package.json     # Project configuration and dependencies
```

## Technology Stack

- **Framework:** React 18 with TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React Context API
- **Routing:** React Router v6
- **UI Components:** Headless UI and Heroicons
- **HTTP Client:** Axios
- **Testing:** Jest and React Testing Library
- **Code Quality:** ESLint, Prettier

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm start
   ```

3. Run tests:
   ```bash
   npm test
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Component Guidelines

1. **File Structure:**
   ```typescript
   // MyComponent.tsx
   import React from 'react';
   import { MyComponentProps } from './types';
   import styles from './styles.module.css';
   
   export const MyComponent: React.FC<MyComponentProps> = ({ prop1, prop2 }) => {
     return (
       <div className={styles.container}>
         {/* Component content */}
       </div>
     );
   };
   ```

2. **Props Interface:**
   ```typescript
   // types.ts
   export interface MyComponentProps {
     prop1: string;
     prop2?: number;
     onEvent?: (value: string) => void;
   }
   ```

3. **Styling:**
   - Use Tailwind CSS utility classes for styling
   - Create custom components for repeated patterns
   - Follow BEM naming convention for custom CSS

## State Management

- Use React Context for global state
- Keep state as close to where it's used as possible
- Use custom hooks to encapsulate complex state logic

## Testing

- Write tests for all components and utilities
- Follow Testing Library best practices
- Aim for high test coverage on critical paths

## Code Quality

- Run linter before committing:
  ```bash
  npm run lint
  ```

- Format code:
  ```bash
  npm run format
  ```

## API Integration

- Use services directory for API calls
- Implement proper error handling
- Use TypeScript interfaces for API responses

## Performance Considerations

- Implement code splitting for routes
- Use React.lazy for dynamic imports
- Optimize images and assets
- Implement proper caching strategies

## Accessibility

- Follow WCAG 2.1 guidelines
- Use semantic HTML elements
- Implement proper ARIA attributes
- Ensure keyboard navigation works

## Browser Support

- Support latest versions of:
  - Chrome
  - Firefox
  - Safari
  - Edge

## Contributing

1. Follow the style guide
2. Write meaningful commit messages
3. Add tests for new features
4. Update documentation as needed
