import { runHistory } from '../data/mockTests';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

export function HistoryPage() {
  return (
    <div className="max-w-4xl space-y-4">
      <p className="text-sm text-gray-500">Complete history of all test runs.</p>

      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Run</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Triggered By</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Duration</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Passed</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Failed</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {runHistory.map(run => (
                <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900">{run.runAt}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                      {run.triggeredBy}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-500">{(run.duration / 1000).toFixed(1)}s</td>
                  <td className="px-5 py-3 text-gray-700">{run.total}</td>
                  <td className="px-5 py-3 text-emerald-600 font-medium">{run.passed}</td>
                  <td className="px-5 py-3 text-red-500 font-medium">{run.failed > 0 ? run.failed : '—'}</td>
                  <td className="px-5 py-3">
                    <Badge status={run.failed === 0 ? 'pass' : 'fail'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
