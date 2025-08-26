import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { ErrorProvider } from './context/ErrorContext';
import ErrorBoundary from './components/error/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import GraphListPage from './pages/GraphListPage';
import GraphEditor from './pages/GraphEditor';
import MainLayout from './components/layout/MainLayout';
import BackendStatusIndicator from './components/layout/BackendStatusIndicator';
import './App.css';

// Protected route component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // In a real app, you would check the authentication status here
  // For now, we'll just check if the user is on the login page
  const isAuthenticated = window.location.pathname !== '/';
  
  return isAuthenticated ? (
    <MainLayout>{children}</MainLayout>
  ) : (
    <Navigate to="/" replace />
  );
};

function App() {
  return (
    <ErrorBoundary>
      <ErrorProvider>
        <AppProvider>
          <Router>
            <div className="app">
              <Routes>
                <Route path="/" element={<LoginPage />} />
                <Route
                  path="/graphs"
                  element={
                    <ProtectedRoute>
                      <GraphListPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/editor"
                  element={
                    <ProtectedRoute>
                      <GraphEditor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/editor/:graphId"
                  element={
                    <ProtectedRoute>
                      <GraphEditor />
                    </ProtectedRoute>
                  }
                />
                {/* Redirect any unknown paths to /graphs */}
                <Route path="*" element={<Navigate to="/graphs" replace />} />
              </Routes>
              <BackendStatusIndicator />
            </div>
          </Router>
        </AppProvider>
      </ErrorProvider>
    </ErrorBoundary>
  );
}

export default App;
