import { useReducer } from 'react';
import type { ReactNode } from 'react';
import { AppContext, type AppState, type AppAction } from './context';

const initialState: AppState = {
  tenantId: 'evil-corp',
  currentGraph: null,
  selectedNodeId: null,
  selectedFile: null,
  selectedTool: null,
  isLoading: false,
  error: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_TENANT_ID':
      return { ...state, tenantId: action.payload };
    case 'SET_CURRENT_GRAPH':
      return { ...state, currentGraph: action.payload };
    case 'SET_SELECTED_NODE':
      return { ...state, selectedNodeId: action.payload };
    case 'SET_SELECTED_FILE':
      return { ...state, selectedFile: action.payload };
    case 'SET_SELECTED_TOOL':
      return { ...state, selectedTool: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'UPDATE_FILE_CONTENT':
      if (!state.currentGraph) return state;
      
      const { fileName, content } = action.payload;
      const updatedGraph = { ...state.currentGraph };
      
      // Update file in plans
      updatedGraph.plans = updatedGraph.plans.map(plan => ({
        ...plan,
        files: plan.files.map(file => 
          file.name === fileName ? { ...file, contents: content } : file
        )
      }));
      
      // Update file in tasks
      updatedGraph.tasks = updatedGraph.tasks.map(task => ({
        ...task,
        files: task.files.map(file => 
          file.name === fileName ? { ...file, contents: content } : file
        )
      }));
      
      // Update selected file if it matches
      const updatedSelectedFile = state.selectedFile?.name === fileName 
        ? { ...state.selectedFile, contents: content }
        : state.selectedFile;
      
      return { 
        ...state, 
        currentGraph: updatedGraph,
        selectedFile: updatedSelectedFile
      };
    default:
      return state;
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}