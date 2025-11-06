/**
 * Deployment History Page
 * View deployment history and status
 * (Placeholder - to be fully implemented in next phase)
 */

import { History } from 'lucide-react';

const DeploymentHistoryPage = () => {
  return (
    <div className="max-w-7xl">
      <div className="text-center py-16">
        <History size={64} className="mx-auto text-green-600 mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Deployment History</h1>
        <p className="text-gray-600 mb-4">
          View all form deployments and their status
        </p>
        <p className="text-gray-500">
          This feature is under development. Coming soon!
        </p>
      </div>
    </div>
  );
};

export default DeploymentHistoryPage;
