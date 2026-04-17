import { clsx } from 'clsx';
import type { TestStatus } from '../../types';

interface BadgeProps {
  status: TestStatus;
  className?: string;
}

const config: Record<TestStatus, { label: string; classes: string }> = {
  pass:    { label: 'Pass',    classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20' },
  fail:    { label: 'Fail',    classes: 'bg-red-50 text-red-700 ring-red-600/20' },
  warning: { label: 'Warning', classes: 'bg-amber-50 text-amber-700 ring-amber-600/20' },
  pending: { label: 'Pending', classes: 'bg-slate-100 text-slate-600 ring-slate-500/20' },
  running: { label: 'Running', classes: 'bg-blue-50 text-blue-700 ring-blue-600/20 animate-pulse' },
};

export function Badge({ status, className }: BadgeProps) {
  const { label, classes } = config[status];
  return (
    <span className={clsx(
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
      classes,
      className
    )}>
      {label}
    </span>
  );
}
