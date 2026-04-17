import { clsx } from 'clsx';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Globe, FileText, ShieldCheck,
  Zap, History, Settings, X
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const navItems = [
  { label: 'Dashboard',      icon: LayoutDashboard, path: '/' },
  { label: 'Website Tests',  icon: Globe,            path: '/website' },
  { label: 'Form Tests',     icon: FileText,         path: '/forms' },
  { label: 'Security',       icon: ShieldCheck,      path: '/security' },
  { label: 'APIs',           icon: Zap,              path: '/apis' },
  { label: 'History',        icon: History,          path: '/history' },
  { label: 'Settings',       icon: Settings,         path: '/settings' },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed inset-y-0 left-0 z-30 w-64 flex flex-col bg-slate-900 transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 lg:flex lg:shrink-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Branding */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/60">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-xl shrink-0">
              🧪
            </div>
            <div className="min-w-0">
              <p className="text-white text-sm font-bold leading-tight truncate">TutorCare Tests</p>
              <p className="text-slate-400 text-xs">Testing Dashboard</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white transition-colors p-1 rounded"
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          <p className="px-3 pt-2 pb-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Navigation
          </p>
          {navItems.map(({ label, icon: Icon, path }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              onClick={onClose}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-100',
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              )}
            >
              <Icon size={16} className="shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status strip */}
        <div className="p-4 border-t border-slate-700/60">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-slate-800">
            <div className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
            <div className="min-w-0">
              <p className="text-xs text-slate-500 leading-none mb-0.5">Status</p>
              <p className="text-xs text-slate-300 font-medium truncate">All systems operational</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
