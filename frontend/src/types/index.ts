export type TestStatus = 'pass' | 'fail' | 'warning' | 'pending' | 'running';
export type TestCategory = 'website' | 'form' | 'security' | 'api';

export interface TestResult {
  id: string;
  name: string;
  category: TestCategory;
  status: TestStatus;
  lastRun: string;
  duration: number; // ms
  description: string;
  url?: string;
  details?: string;
  errorMessage?: string;
}

export interface TestSection {
  id: string;
  title: string;
  category: TestCategory;
  icon: string;
  tests: TestResult[];
}

export interface SummaryStats {
  total: number;
  passed: number;
  failed: number;
  warnings: number;
  lastRun: string;
}

export interface RunHistoryEntry {
  id: string;
  runAt: string;
  duration: number;
  total: number;
  passed: number;
  failed: number;
  triggeredBy: string;
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}
