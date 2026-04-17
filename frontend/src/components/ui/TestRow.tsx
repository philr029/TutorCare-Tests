import { useState } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { Badge } from './Badge';
import type { TestResult } from '../../types';

interface TestRowProps {
  test: TestResult;
}

export function TestRow({ test }: TestRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="hover:bg-gray-50 transition-colors cursor-pointer group"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 group-hover:text-gray-600 transition-colors">
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </span>
            <span className="text-sm font-medium text-gray-900">{test.name}</span>
          </div>
        </td>
        <td className="px-4 py-3">
          <span className={clsx(
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
            {
              website: 'bg-blue-50 text-blue-700 ring-blue-600/20',
              form: 'bg-purple-50 text-purple-700 ring-purple-600/20',
              security: 'bg-orange-50 text-orange-700 ring-orange-600/20',
              api: 'bg-cyan-50 text-cyan-700 ring-cyan-600/20',
            }[test.category]
          )}>
            {test.category.charAt(0).toUpperCase() + test.category.slice(1)}
          </span>
        </td>
        <td className="px-4 py-3">
          <Badge status={test.status} />
        </td>
        <td className="px-4 py-3 text-sm text-gray-500">{test.lastRun}</td>
        <td className="px-4 py-3 text-sm text-gray-500">
          {test.duration > 0 ? `${test.duration}ms` : '—'}
        </td>
        <td className="px-4 py-3">
          {test.url && (
            <a
              href={test.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 transition-colors"
              onClick={e => e.stopPropagation()}
            >
              <ExternalLink size={14} />
            </a>
          )}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-gray-50 border-t border-gray-100">
          <td colSpan={6} className="px-8 py-3">
            <div className="text-sm text-gray-600 space-y-1">
              <p><span className="font-medium text-gray-700">Description:</span> {test.description}</p>
              {test.errorMessage && (
                <p className="text-red-600">
                  <span className="font-medium">Error:</span> {test.errorMessage}
                </p>
              )}
              {test.details && (
                <p className="text-amber-700">
                  <span className="font-medium">Details:</span> {test.details}
                </p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
