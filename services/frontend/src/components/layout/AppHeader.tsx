import React from 'react';
import { useAppContext } from '../../hooks/useAppContext';
import './AppHeader.css';

const AppHeader: React.FC = () => {
  const { state } = useAppContext();

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="app-title">Agentic Framework</h1>
          <span className="tenant-id">Tenant: {state.tenantId}</span>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;