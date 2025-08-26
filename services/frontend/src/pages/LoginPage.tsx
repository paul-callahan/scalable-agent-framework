import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../hooks/useAppContext';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // For now, just navigate to graphs page
    // In the future, this would validate credentials
    navigate('/graphs');
  };

  const handleTenantChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_TENANT_ID', payload: e.target.value });
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="app-title">Agentic Framework</h1>
          <p className="app-subtitle">Scalable Agent Workflow Management</p>
        </div>
        
        <form className="login-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              disabled
              className="disabled-field"
            />
            <small className="field-note">Authentication not yet implemented</small>
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              disabled
              className="disabled-field"
            />
            <small className="field-note">Authentication not yet implemented</small>
          </div>
          
          <div className="form-group">
            <label htmlFor="tenant">Tenant ID</label>
            <input
              id="tenant"
              type="text"
              value={state.tenantId}
              onChange={handleTenantChange}
              placeholder="Enter tenant ID"
              className="enabled-field"
            />
            <small className="field-note">Default: evil-corp</small>
          </div>
          
          <button type="submit" className="login-button">
            Login
          </button>
        </form>
        
        <div className="login-footer">
          <p>Welcome to the Agentic Framework</p>
          <p>Build and manage scalable agent workflows</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
