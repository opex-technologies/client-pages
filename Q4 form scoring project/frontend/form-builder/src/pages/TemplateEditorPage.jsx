/**
 * Template Editor Page
 * Create and edit form templates
 * (Placeholder - to be fully implemented in next phase)
 */

import { useParams } from 'react-router-dom';
import { Construction } from 'lucide-react';

const TemplateEditorPage = () => {
  const { id } = useParams();

  return (
    <div className="max-w-7xl">
      <div className="text-center py-16">
        <Construction size={64} className="mx-auto text-opex-navy mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Template Editor</h1>
        <p className="text-gray-600 mb-4">
          {id ? `Editing template: ${id}` : 'Creating new template'}
        </p>
        <p className="text-gray-500">
          This feature is under development. Coming soon!
        </p>
      </div>
    </div>
  );
};

export default TemplateEditorPage;
