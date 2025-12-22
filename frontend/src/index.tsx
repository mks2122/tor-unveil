import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ClerkProvider } from '@clerk/clerk-react';

// Import Clerk Publishable Key
const clerkPubKey = "pk_test_c2F2ZWQtbXVkZmlzaC0zMS5jbGVyay5hY2NvdW50cy5kZXYk";

if (!clerkPubKey) {
  throw new Error("Missing Clerk Publishable Key. Please add REACT_APP_CLERK_PUBLISHABLE_KEY to your .env file");
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <ClerkProvider publishableKey={clerkPubKey}>
      <App />
    </ClerkProvider>
  </React.StrictMode>
);
