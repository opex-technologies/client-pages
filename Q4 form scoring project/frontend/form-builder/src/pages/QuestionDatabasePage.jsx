/**
 * Question Database Page
 * Browse and search questions
 * (Placeholder - to be fully implemented in next phase)
 */

import { Database } from 'lucide-react';

const QuestionDatabasePage = () => {
  return (
    <div className="max-w-7xl">
      <div className="text-center py-16">
        <Database size={64} className="mx-auto text-opex-cyan mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Question Database</h1>
        <p className="text-gray-600 mb-4">
          Browse 1,041 available questions for your forms
        </p>
        <p className="text-gray-500">
          This feature is under development. Coming soon!
        </p>
      </div>
    </div>
  );
};

export default QuestionDatabasePage;
