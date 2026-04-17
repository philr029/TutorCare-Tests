import { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export function SettingsPage() {
  const [apiUrl, setApiUrl] = useState('https://api.tutorcare.com');
  const [env, setEnv] = useState('staging');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl space-y-6">
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">API Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              API Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Environment
            </label>
            <select
              value={env}
              onChange={e => setEnv(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition bg-white"
            >
              <option value="staging">Staging</option>
              <option value="production">Production</option>
              <option value="development">Development</option>
            </select>
          </div>
        </div>
        <div className="mt-5 flex items-center gap-3">
          <Button variant="primary" size="md" onClick={handleSave}>
            {saved ? '✓ Saved' : 'Save Settings'}
          </Button>
        </div>
      </Card>

      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Test Schedule</h3>
        <div className="space-y-3">
          {['Every 15 minutes', 'Every hour', 'Every 6 hours', 'Daily'].map(option => (
            <label key={option} className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="schedule"
                defaultChecked={option === 'Every hour'}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
              />
              <span className="text-sm text-gray-700">{option}</span>
            </label>
          ))}
        </div>
      </Card>
    </div>
  );
}
