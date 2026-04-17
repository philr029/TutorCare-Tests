import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { clsx } from 'clsx';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';
import type { TestSection, TestResult } from '../../types';

interface TestSectionCardProps {
  section: TestSection;
}

export function TestSectionCard({ section }: TestSectionCardProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [running, setRunning] = useState(false);

  const passed = section.tests.filter(t => t.status === 'pass').length;
  const failed = section.tests.filter(t => t.status === 'fail').length;
  const warnings = section.tests.filter(t => t.status === 'warning').length;
  const total = section.tests.length;

  const overallStatus = failed > 0 ? 'fail' : warnings > 0 ? 'warning' : 'pass';

  const handleRun = () => {
    setRunning(true);
    setTimeout(() => setRunning(false), 2000);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Card header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <span className="text-xl">{section.icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-900">{section.title}</h3>
              <Badge status={overallStatus} />
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              {passed}/{total} passed
              {failed > 0 && ` · ${failed} failed`}
              {warnings > 0 && ` · ${warnings} warnings`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" loading={running} onClick={handleRun}>
            {running ? 'Running…' : 'Run'}
          </Button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100 flex">
        <div
          className="bg-emerald-400 transition-all duration-500"
          style={{ width: `${(passed / total) * 100}%` }}
        />
        {warnings > 0 && (
          <div
            className="bg-amber-400 transition-all duration-500"
            style={{ width: `${(warnings / total) * 100}%` }}
          />
        )}
        {failed > 0 && (
          <div
            className="bg-red-400 transition-all duration-500"
            style={{ width: `${(failed / total) * 100}%` }}
          />
        )}
      </div>

      {/* Test list */}
      {!collapsed && (
        <div className="divide-y divide-gray-50">
          {section.tests.length === 0 ? (
            <EmptyState title="No tests" description="No tests defined for this section yet." icon="📭" />
          ) : (
            section.tests.map(test => (
              <TestItem key={test.id} test={test} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function TestItem({ test }: { test: TestResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <div
        className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors cursor-pointer group"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={clsx(
            'w-1.5 h-1.5 rounded-full shrink-0',
            {
              pass: 'bg-emerald-400',
              fail: 'bg-red-400',
              warning: 'bg-amber-400',
              pending: 'bg-gray-300',
              running: 'bg-blue-400 animate-pulse',
            }[test.status]
          )} />
          <span className="text-sm text-gray-800 font-medium truncate">{test.name}</span>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-3">
          <span className="text-xs text-gray-400 hidden sm:inline">{test.lastRun}</span>
          {test.duration > 0 && (
            <span className="text-xs text-gray-400 hidden sm:inline">{test.duration}ms</span>
          )}
          <Badge status={test.status} />
        </div>
      </div>
      {expanded && (
        <div className="px-10 py-3 bg-gray-50 border-t border-gray-100 text-sm text-gray-600 space-y-1">
          <p>{test.description}</p>
          {test.errorMessage && (
            <p className="text-red-600 text-xs font-medium mt-1">⚠ {test.errorMessage}</p>
          )}
          {test.details && (
            <p className="text-amber-700 text-xs font-medium mt-1">ℹ {test.details}</p>
          )}
          {test.url && (
            <a
              href={test.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:underline text-xs font-medium inline-block mt-1"
              onClick={e => e.stopPropagation()}
            >
              {test.url} ↗
            </a>
          )}
        </div>
      )}
    </>
  );
}
