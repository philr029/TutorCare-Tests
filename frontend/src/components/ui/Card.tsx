import { clsx } from 'clsx';
import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export function Card({ children, className, padding = 'md', hover = false }: CardProps) {
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-5',
    lg: 'p-6',
  };

  return (
    <div className={clsx(
      'bg-white rounded-xl border border-gray-200 shadow-sm',
      hover && 'hover:shadow-md hover:border-gray-300 transition-all duration-150 cursor-pointer',
      paddings[padding],
      className
    )}>
      {children}
    </div>
  );
}
