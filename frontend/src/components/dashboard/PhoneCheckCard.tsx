import { useState } from 'react';
import { Phone } from 'lucide-react';
import { clsx } from 'clsx';
import { Button } from '../ui/Button';
import { checkPhone } from '../../services/api';
import type { PhoneCheckResult } from '../../types';

type UIState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; input: string; data: PhoneCheckResult }
  | { status: 'error'; message: string };

function ResultRow({ label, value }: { label: string; value: string | boolean }) {
  const display = String(value);
  return (
    <div className="flex items-start justify-between gap-2 py-1.5">
      <span className="text-xs text-gray-500 font-medium shrink-0">{label}</span>
      <span
        className="text-xs text-gray-800 text-right font-medium truncate max-w-[60%]"
        title={display}
      >
        {display}
      </span>
    </div>
  );
}

export function PhoneCheckCard() {
  const [phone, setPhone] = useState('');
  const [state, setState] = useState<UIState>({ status: 'idle' });

  const handleRun = async () => {
    const trimmed = phone.trim();
    if (!trimmed) return;
    setState({ status: 'loading' });
    const result = await checkPhone(trimmed);
    if (result.success) {
      setState({ status: 'success', input: result.input, data: result.provider });
    } else {
      setState({ status: 'error', message: result.error });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleRun();
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
        <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
          <Phone size={18} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Phone Number Check</h3>
          <p className="text-xs text-gray-400 mt-0.5">Validate via NumVerify API</p>
        </div>
      </div>

      {/* Input row */}
      <div className="px-5 py-4 flex gap-2">
        <input
          type="tel"
          value={phone}
          onChange={e => setPhone(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="+44 7911 123456"
          className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent placeholder:text-gray-300"
          disabled={state.status === 'loading'}
        />
        <Button
          variant="primary"
          size="sm"
          loading={state.status === 'loading'}
          onClick={handleRun}
          disabled={!phone.trim() || state.status === 'loading'}
        >
          {state.status === 'loading' ? 'Checking…' : 'Run Check'}
        </Button>
      </div>

      {/* Results / states */}
      <div className="px-5 pb-5">
        {state.status === 'idle' && (
          <p className="text-xs text-gray-400 text-center py-4">
            Enter a phone number above and click <strong>Run Check</strong>.
          </p>
        )}

        {state.status === 'loading' && (
          <div className="flex items-center justify-center gap-2 py-4 text-indigo-600">
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-sm font-medium">Running test…</span>
          </div>
        )}

        {state.status === 'error' && (
          <div className="rounded-lg bg-red-50 border border-red-100 px-4 py-3 flex items-start gap-2">
            <span className="text-red-500 text-sm shrink-0">⚠</span>
            <p className="text-sm text-red-700 font-medium">{state.message}</p>
          </div>
        )}

        {state.status === 'success' && (
          <div className="space-y-3">
            {/* Valid / invalid badge */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 font-medium">Checked number</span>
              <span className="text-xs text-gray-800 font-mono font-medium">{state.input}</span>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset',
                  state.data.valid
                    ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'
                    : 'bg-red-50 text-red-700 ring-red-600/20',
                )}
              >
                {state.data.valid ? '✓ Valid' : '✗ Invalid'}
              </span>
              {state.data.line_type && (
                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/20 capitalize">
                  {state.data.line_type}
                </span>
              )}
            </div>

            {/* Detail rows */}
            <div className="bg-gray-50 rounded-lg px-4 py-2 divide-y divide-gray-100">
              {state.data.country_name && (
                <ResultRow label="Country" value={state.data.country_name} />
              )}
              {state.data.location && (
                <ResultRow label="Location" value={state.data.location} />
              )}
              {state.data.carrier && (
                <ResultRow label="Carrier" value={state.data.carrier} />
              )}
              {state.data.international_format && (
                <ResultRow label="International" value={state.data.international_format} />
              )}
              {state.data.local_format && (
                <ResultRow label="Local" value={state.data.local_format} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
