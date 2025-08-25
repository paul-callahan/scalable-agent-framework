import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppContext } from '../../hooks/useAppContext';
import './AppHeader.css';

const AppHeader: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const navigate = useNavigate();
  const location = useLocation();

  const handleTenantChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_TENANT_ID', payload: event.target.value });
  };

  const handleNavigateToManagement = () => {
    navigate('/');
  };

  const handleNavigateToEditor = () => {
    navigate('/editor');
  };

  const isOnManagement = location.pathname === '/';
  const isOnEditor = location.pathname.startsWith('/editor');

  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="app-title">Agent Graph Composer</h1>
        <nav className="header-nav">
          <button
            className={`nav-button ${isOnManagement ? 'active' : ''}`}
            onClick={handleNavigateToManagement}
          >
            Management
          </button>
          <button
            className={`nav-button ${isOnEditor ? 'active' : ''}`}
            onClick={handleNavigateToEditor}
          >
            Editor
          </button>
        </nav>
      </div>
      
      <div className="header-right">
        <div className="tenant-input">
          <label htmlFor="tenantId">Tenant ID:</label>
          <input
            id="tenantId"
            type="text"
            value={state.tenantId}
            onChange={handleTenantChange}
            placeholder="evil-corp"
          />
        </div>
      </div>
    </header>
  );
};

export default AppHeader;