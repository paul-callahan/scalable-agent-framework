import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import ErrorNotification from '../components/error/ErrorNotification';
import type { ErrorNotificationProps } from '../components/error/ErrorNotification';

interface ErrorContextType {
  showError: (message: string, options?: Partial<ErrorNotificationProps>) => void;
  showWarning: (message: string, options?: Partial<ErrorNotificationProps>) => void;
  showInfo: (message: string, options?: Partial<ErrorNotificationProps>) => void;
  clearErrors: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

interface ErrorNotificationState extends ErrorNotificationProps {
  id: string;
}

interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<ErrorNotificationState[]>([]);

  const addNotification = (
    message: string,
    type: 'error' | 'warning' | 'info',
    options: Partial<ErrorNotificationProps> = {}
  ) => {
    const id = Date.now().toString();
    const notification: ErrorNotificationState = {
      id,
      message,
      type,
      duration: 5000,
      ...options,
      onClose: () => {
        removeNotification(id);
        options.onClose?.();
      },
    };

    setNotifications(prev => [...prev, notification]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const showError = (message: string, options?: Partial<ErrorNotificationProps>) => {
    addNotification(message, 'error', options);
  };

  const showWarning = (message: string, options?: Partial<ErrorNotificationProps>) => {
    addNotification(message, 'warning', options);
  };

  const showInfo = (message: string, options?: Partial<ErrorNotificationProps>) => {
    addNotification(message, 'info', options);
  };

  const clearErrors = () => {
    setNotifications([]);
  };

  return (
    <ErrorContext.Provider value={{ showError, showWarning, showInfo, clearErrors }}>
      {children}
      <div className="error-notifications-container">
        {notifications.map(notification => (
          <ErrorNotification
            key={notification.id}
            {...notification}
          />
        ))}
      </div>
    </ErrorContext.Provider>
  );
};

export const useError = (): ErrorContextType => {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};