import React, { useEffect, useState } from 'react';
import './ErrorNotification.css';

export interface ErrorNotificationProps {
  message: string;
  type?: 'error' | 'warning' | 'info';
  duration?: number;
  onClose?: () => void;
  retryAction?: {
    label: string;
    action: () => void;
  };
}

const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  message,
  type = 'error',
  duration = 5000,
  onClose,
  retryAction,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onClose?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    onClose?.();
  };

  const handleRetry = () => {
    retryAction?.action();
    handleClose();
  };

  if (!isVisible) {
    return null;
  }

  const getIcon = () => {
    switch (type) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  return (
    <div className={`error-notification error-notification--${type}`}>
      <div className="error-notification__content">
        <span className="error-notification__icon">{getIcon()}</span>
        <span className="error-notification__message">{message}</span>
      </div>
      <div className="error-notification__actions">
        {retryAction && (
          <button
            className="error-notification__button error-notification__button--retry"
            onClick={handleRetry}
          >
            {retryAction.label}
          </button>
        )}
        <button
          className="error-notification__button error-notification__button--close"
          onClick={handleClose}
          aria-label="Close notification"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;