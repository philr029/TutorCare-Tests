import { StatCard } from '../components/ui/StatCard';
import { TestSectionCard } from '../components/dashboard/TestSectionCard';
import { testSections, computeSummary, runHistory } from '../data/mockTests';
import { Badge } from '../components/ui/Badge';
import type { RunHistoryEntry } from '../types';

export function DashboardPage() {
  const stats = computeSummary();

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Checks"
          value={stats.total}
          icon="🔢"
          color="indigo"
          subtitle="Across all categories"
        />
        <StatCard
          title="Passed"
          value={stats.passed}
          icon="✅"
          color="emerald"
          subtitle={`${Math.round((stats.passed / stats.total) * 100)}% pass rate`}
        />
        <StatCard
          title="Failed"
          value={stats.failed}
          icon="❌"
          color="red"
          subtitle="Need attention"
        />
        <StatCard
          title="Last Run"
          value={stats.lastRun}
          icon="🕐"
          color="slate"
          subtitle="Automated run"
        />
      </div>

      {/* Test sections */}
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-3">Test Suites</h2>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {testSections.map(section => (
            <TestSectionCard key={section.id} section={section} />
          ))}
        </div>
      </div>

      {/* Recent runs */}
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-3">Recent Test Runs</h2>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Run Time</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Triggered By</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Duration</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Results</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {runHistory.map((run: RunHistoryEntry) => (
                  <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{run.runAt}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                        {run.triggeredBy}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{(run.duration / 1000).toFixed(1)}s</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-emerald-600 font-medium">{run.passed} passed</span>
                        {run.failed > 0 && <span className="text-red-500 font-medium">{run.failed} failed</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge status={run.failed === 0 ? 'pass' : 'fail'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
