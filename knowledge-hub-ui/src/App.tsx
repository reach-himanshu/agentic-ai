import { ThemeProvider } from './context/ThemeContext';
import { KnowledgeHub } from './pages/KnowledgeHub';
import './index.css';

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
        <KnowledgeHub />
      </div>
    </ThemeProvider>
  );
}

export default App;
