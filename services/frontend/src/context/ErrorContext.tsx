import React, { createContext, useContext, useState, useRef } from 'react';
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
  const recentMessages = useRef<Set<string>>(new Set());
  const messageTimeouts = useRef<Map<string, number>>(new Map());

  const addNotification = (
    message: string,
    type: 'error' | 'warning' | 'info',
    options: Partial<ErrorNotificationProps> = {}
  ) => {
    // Check if this message was recently shown (within last 5 seconds)
    const messageKey = `${type}:${message}`;
    if (recentMessages.current.has(messageKey)) {
      console.log('Suppressing duplicate notification:', message);
      return;
    }

    // Add message to recent set and set timeout to remove it
    recentMessages.current.add(messageKey);
    const timeout = setTimeout(() => {
      recentMessages.current.delete(messageKey);
      messageTimeouts.current.delete(messageKey);
    }, 5000); // 5 second deduplication window
    
    messageTimeouts.current.set(messageKey, timeout);

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
    // Clear all timeouts
    messageTimeouts.current.forEach(timeout => clearTimeout(timeout));
    messageTimeouts.current.clear();
    recentMessages.current.clear();
    
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