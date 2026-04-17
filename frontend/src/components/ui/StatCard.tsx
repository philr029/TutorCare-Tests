import { clsx } from 'clsx';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'indigo' | 'emerald' | 'red' | 'amber' | 'slate';
  subtitle?: string;
}

const colorMap = {
  indigo: { icon: 'bg-indigo-50 text-indigo-600', value: 'text-indigo-600' },
  emerald: { icon: 'bg-emerald-50 text-emerald-600', value: 'text-emerald-600' },
  red: { icon: 'bg-red-50 text-red-600', value: 'text-red-600' },
  amber: { icon: 'bg-amber-50 text-amber-600', value: 'text-amber-600' },
  slate: { icon: 'bg-slate-100 text-slate-600', value: 'text-slate-700' },
};

export function StatCard({ title, value, icon, color = 'indigo', subtitle }: StatCardProps) {
  const colors = colorMap[color];
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-start gap-4 hover:shadow-md transition-shadow duration-150">
      <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center text-xl shrink-0', colors.icon)}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-gray-500 font-medium truncate">{title}</p>
        <p className={clsx('text-3xl font-bold mt-0.5', colors.value)}>{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}
