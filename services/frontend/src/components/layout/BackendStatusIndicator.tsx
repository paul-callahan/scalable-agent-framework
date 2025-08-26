import React, { useState, useEffect } from 'react';
import { graphApi } from '../../api/client';
import { useAppContext } from '../../hooks/useAppContext';
import './BackendStatusIndicator.css';

type BackendStatus = 'unknown' | 'available' | 'unavailable';

const BackendStatusIndicator: React.FC = () => {
  const { state } = useAppContext();
  const [status, setStatus] = useState<BackendStatus>('unknown');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkBackendStatus = async () => {
    try {
      await graphApi.listGraphs(state.tenantId);
      setStatus('available');
      setLastCheck(new Date());
    } catch (error) {
      setStatus('unavailable');
      setLastCheck(new Date());
    }
  };

  // Check backend status on mount and every 30 seconds
  useEffect(() => {
    checkBackendStatus();
    
    const interval = setInterval(checkBackendStatus, 30000);
    
    return () => clearInterval(interval);
  }, [state.tenantId]);

  const getStatusDisplay = () => {
    switch (status) {
      case 'available':
        return { text: 'Backend Online', className: 'status-online', icon: '🟢' };
      case 'unavailable':
        return { text: 'Backend Offline', className: 'status-offline', icon: '🔴' };
      default:
        return { text: 'Checking...', className: 'status-checking', icon: '🟡' };
    }
  };

  const statusInfo = getStatusDisplay();

  return (
    <div className={`backend-status-indicator ${statusInfo.className}`}>
      <span className="status-icon">{statusInfo.icon}</span>
      <span className="status-text">{statusInfo.text}</span>
      {lastCheck && (
        <span className="last-check">
          Last check: {lastCheck.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

export default BackendStatusIndicator;
