import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { ErrorProvider } from './context/ErrorContext';
import ErrorBoundary from './components/error/ErrorBoundary';
import GraphManagement from './pages/GraphManagement';
import GraphEditor from './pages/GraphEditor';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <ErrorProvider>
        <AppProvider>
          <Router>
            <div className="app">
              <Routes>
                <Route path="/" element={<GraphManagement />} />
                <Route path="/editor" element={<GraphEditor />} />
                <Route path="/editor/:graphId" element={<GraphEditor />} />
              </Routes>
            </div>
          </Router>
        </AppProvider>
      </ErrorProvider>
    </ErrorBoundary>
  );
}

export default App;
