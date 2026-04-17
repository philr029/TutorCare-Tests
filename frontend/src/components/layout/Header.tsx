import { Menu, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { Button } from '../ui/Button';

interface HeaderProps {
  onMenuClick: () => void;
  title?: string;
}

export function Header({ onMenuClick, title = 'Dashboard' }: HeaderProps) {
  const [running, setRunning] = useState(false);

  const handleRunAll = () => {
    setRunning(true);
    setTimeout(() => setRunning(false), 3000);
  };

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 py-4 bg-white border-b border-gray-200 shrink-0 shadow-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-1.5 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
        >
          <Menu size={20} />
        </button>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-lg font-bold text-gray-900">{title}</h1>
            <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-700/10">
              Staging
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">
            Last updated: <span className="text-gray-600 font-medium">30 seconds ago</span>
          </p>
        </div>
      </div>

      <Button
        variant="primary"
        size="sm"
        loading={running}
        onClick={handleRunAll}
      >
        <RefreshCw size={14} />
        {running ? 'Running…' : 'Run All Tests'}
      </Button>
    </header>
  );
}
