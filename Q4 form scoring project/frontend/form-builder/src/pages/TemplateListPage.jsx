/**
 * Template List Page
 * Displays all form templates with filtering and search
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, BarChart3 } from 'lucide-react';
import { formBuilderAPI } from '../services/formBuilderApi';
import toast from 'react-hot-toast';
import ConfirmDialog from '../components/ConfirmDialog';

const TemplateListPage = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

  useEffect(() => {
    fetchTemplates();
  }, [filterStatus, filterType]);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const params = {};
      if (filterStatus !== 'all') params.status = filterStatus;
      if (filterType !== 'all') params.opportunity_type = filterType;

      const response = await formBuilderAPI.getTemplates(params);

      if (response.data.success) {
        setTemplates(response.data.data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTemplates = templates.filter((template) =>
    template.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.opportunity_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.opportunity_subtype.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteTemplate = async (templateId) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Template',
      message: 'Are you sure you want to delete this template? This action cannot be undone.',
      onConfirm: async () => {
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });
        try {
          await formBuilderAPI.deleteTemplate(templateId);
          toast.success('Template deleted successfully');
          fetchTemplates();
        } catch (error) {
          console.error('Failed to delete template:', error);
          toast.error(error.response?.data?.error?.message || 'Failed to delete template');
        }
      }
    });
  };

  const TemplateCard = ({ template }) => (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 mb-1">
            {template.template_name}
          </h3>
          <p className="text-sm text-gray-600">
            {template.opportunity_type} • {template.opportunity_subtype}
          </p>
        </div>
        <span
          className={`px-3 py-1 text-xs font-medium rounded-full ${
            template.status === 'published'
              ? 'bg-green-100 text-green-800'
              : template.status === 'draft'
              ? 'bg-yellow-100 text-yellow-800'
              : template.status === 'archived'
              ? 'bg-gray-100 text-gray-800'
              : 'bg-blue-100 text-blue-800'
          }`}
        >
          {template.status}
        </span>
      </div>

      {template.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {template.description}
        </p>
      )}

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <span>{template.question_count || 0} questions</span>
        <span>{new Date(template.created_at).toLocaleDateString()}</span>
      </div>

      {template.deployed_url && (
        <div className="mb-4 p-2 bg-green-50 rounded-lg">
          <p className="text-xs text-green-700 font-medium mb-1">Deployed URL:</p>
          <a
            href={template.deployed_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-green-600 hover:underline break-all"
          >
            {template.deployed_url}
          </a>
        </div>
      )}

      <div className="flex items-center space-x-2">
        <button
          onClick={() => navigate(`/templates/${template.template_id}/edit`)}
          className="flex-1 btn-secondary text-sm py-2"
        >
          Edit
        </button>
        <button
          onClick={() => navigate(`/templates/${template.template_id}/scoring`)}
          className="flex-1 btn-primary text-sm py-2 flex items-center justify-center gap-1"
          title="Score Responses"
        >
          <BarChart3 size={16} />
          Score
        </button>
        <button
          onClick={() => handleDeleteTemplate(template.template_id)}
          className="btn-danger text-sm py-2 px-3"
          title="Delete Template"
        >
          &times;
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Form Templates</h1>
          <p className="text-gray-600 mt-1">{filteredTemplates.length} templates found</p>
        </div>
        <button
          onClick={() => navigate('/templates/new')}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus size={20} />
          <span>Create New Template</span>
        </button>
      </div>

      {/* Filters and Search */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="md:col-span-1">
            <label className="label">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search templates..."
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className="label">Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field"
            >
              <option value="all">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <label className="label">Opportunity Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input-field"
            >
              <option value="all">All Types</option>
              <option value="Security">Security</option>
              <option value="Network">Network</option>
              <option value="Cloud">Cloud</option>
              <option value="Managed Service Provider">Managed Service Provider</option>
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-48 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <TemplateCard key={template.template_id} template={template} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Filter size={64} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No templates found</h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || filterStatus !== 'all' || filterType !== 'all'
              ? 'Try adjusting your filters'
              : 'Create your first template to get started'}
          </p>
          <button
            onClick={() => navigate('/templates/new')}
            className="btn-primary"
          >
            Create New Template
          </button>
        </div>
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null })}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default TemplateListPage;
