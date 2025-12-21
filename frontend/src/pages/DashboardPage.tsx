import React from 'react';
import { Navigate } from 'react-router-dom';
import { UserButton, useUser, useAuth } from '@clerk/clerk-react';
import Dashboard from '../components/Dashboard';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
  const { user } = useUser();
  const { isSignedIn, isLoaded } = useAuth();
  
  // Show loading state while auth is loading
  if (!isLoaded) {
    return (
      <div className="dashboard-page">
        <div className="loading-container">
          <p>Loading...</p>
        </div>
      </div>
    );
  }
  
  // Redirect to sign in if not authenticated
  if (!isSignedIn) {
    return <Navigate to="/sign-in" replace />;
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>TOR - Unveil Dashboard</h1>
          <div className="header-actions">
            <div className="user-info">
              {user?.primaryEmailAddress?.emailAddress && (
                <span className="user-email">
                  {user.primaryEmailAddress.emailAddress}
                </span>
              )}
              <UserButton afterSignOutUrl="/sign-in" />
            </div>
          </div>
        </div>
      </header>
      <main className="dashboard-main">
        <Dashboard />
      </main>
    </div>
  );
};

export default DashboardPage;
