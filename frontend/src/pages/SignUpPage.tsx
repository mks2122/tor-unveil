import React from 'react';
import { SignUp } from '@clerk/clerk-react';
import './AuthPages.css';

const SignUpPage: React.FC = () => {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>TOR - Unveil</h1>
          <p>Create an account to get started</p>
          <p className="role-info">
            <small>
              🚨 Police accounts: Use @stjosephs.ac.in or @tn.gov.in email
            </small>
          </p>
        </div>
        <SignUp 
          routing="path" 
          path="/sign-up"
          signInUrl="/sign-in"
          afterSignUpUrl="/dashboard"
        />
      </div>
    </div>
  );
};

export default SignUpPage;
