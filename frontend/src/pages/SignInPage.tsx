import React from 'react';
import { SignIn } from '@clerk/clerk-react';
import './AuthPages.css';

const SignInPage: React.FC = () => {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>TOR - Unveil</h1>
          <p>Sign in to access the analysis dashboard</p>
        </div>
        <SignIn 
          routing="path" 
          path="/sign-in"
          signUpUrl="/sign-up"
          afterSignInUrl="/dashboard"
        />
      </div>
    </div>
  );
};

export default SignInPage;
