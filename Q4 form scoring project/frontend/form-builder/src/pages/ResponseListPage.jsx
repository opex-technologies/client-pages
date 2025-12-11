/**
 * Response List Page
 * Displays all form responses with filtering and pagination
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Download, Eye, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { responseScorerAPI, getErrorMessage } from '../services/responseScorerApi';
import ConfirmDialog from '../components/ConfirmDialog';

const ResponseListPage = () => {
  const navigate = useNavigate();
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total_count: 0,
    total_pages: 0
  });

  // Filters
  const [filters, setFilters] = useState({
    template_id: '',
    opportunity_type: '',
    submitter_email: '',
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

  // Load responses
  const loadResponses = async (page = 1) => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pagination.page_size,
        ...filters
      };

      // Add search term to submitter_email filter if provided
      if (searchTerm.trim()) {
        params.submitter_email = searchTerm.trim();
      }

      const response = await responseScorerAPI.getResponses(params);
      console.log('Response Scorer API response:', response);
      console.log('Response data:', response.data);
      const responseData = response.data?.data || response.data || {};
      console.log('Extracted data:', responseData);
      setResponses(responseData.items || []);
      setPagination(responseData.pagination || {
        page: 1,
        page_size: 20,
        total_count: 0,
        total_pages: 0
      });
    } catch (error) {
      console.error('Response Scorer API error:', error);
      console.error('Error response:', error.response);
      toast.error(getErrorMessage(error));
      setResponses([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResponses();
  }, []); // Load on mount

  const handleSearch = (e) => {
    e.preventDefault();
    loadResponses(1); // Reset to page 1 on search
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    loadResponses(1);
    setShowFilters(false);
  };

  const clearFilters = () => {
    setFilters({
      template_id: '',
      opportunity_type: '',
      submitter_email: '',
    });
    setSearchTerm('');
    loadResponses(1);
  };

  const handlePageChange = (newPage) => {
    loadResponses(newPage);
  };

  const handleViewResponse = (responseId) => {
    navigate(`/responses/${responseId}`);
  };

  const handleDeleteResponse = async (responseId) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Response',
      message: 'Are you sure you want to delete this response? This action cannot be undone.',
      onConfirm: async () => {
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });
        try {
          await responseScorerAPI.deleteResponse(responseId);
          toast.success('Response deleted successfully');
          loadResponses(pagination.page);
        } catch (error) {
          toast.error(getErrorMessage(error));
        }
      }
    });
  };

  const handleExport = async () => {
    try {
      const response = await responseScorerAPI.exportResponses(filters);

      // Create blob and download
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `responses_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success('Export downloaded');
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-opex-navy">Form Responses</h1>
        <p className="text-gray-600 mt-2">View and manage survey responses</p>
      </div>

      {/* Search and Actions Bar */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search by submitter email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opex-cyan focus:border-transparent"
              />
            </div>
          </form>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showFilters
                  ? 'bg-opex-cyan text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter size={20} />
              Filters
            </button>

            <button
              onClick={handleExport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <Download size={20} />
              Export
            </button>

            <button
              onClick={() => loadResponses(pagination.page)}
              className="px-4 py-2 bg-opex-navy text-white rounded-lg hover:bg-opex-navy/90 flex items-center gap-2"
            >
              <RefreshCw size={20} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template ID
                </label>
                <input
                  type="text"
                  value={filters.template_id}
                  onChange={(e) => handleFilterChange('template_id', e.target.value)}
                  placeholder="Enter template ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opex-cyan"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Opportunity Type
                </label>
                <select
                  value={filters.opportunity_type}
                  onChange={(e) => handleFilterChange('opportunity_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opex-cyan"
                >
                  <option value="">All Types</option>
                  <option value="Network">Network</option>
                  <option value="Security">Security</option>
                  <option value="Cloud">Cloud</option>
                  <option value="Data Center">Data Center</option>
                  <option value="UCaaS">UCaaS</option>
                  <option value="CCaaS">CCaaS</option>
                  <option value="Expense Management">Expense Management</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Submitter Email
                </label>
                <input
                  type="email"
                  value={filters.submitter_email}
                  onChange={(e) => handleFilterChange('submitter_email', e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opex-cyan"
                />
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={applyFilters}
                className="px-4 py-2 bg-opex-cyan text-white rounded-lg hover:bg-opex-cyan/90"
              >
                Apply Filters
              </button>
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Clear All
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results Summary */}
      <div className="text-sm text-gray-600">
        Showing {responses.length} of {pagination.total_count} responses
      </div>

      {/* Response List */}
      {loading ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-opex-cyan mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading responses...</p>
        </div>
      ) : responses.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <p className="text-gray-600">No responses found</p>
          <button
            onClick={clearFilters}
            className="mt-4 text-opex-cyan hover:text-opex-cyan/80"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Submitter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Template
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type / Subtype
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completion
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Submitted
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {responses.map((response) => (
                <tr key={response.response_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {response.submitter_name || 'Anonymous'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {response.submitter_email || 'No email'}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{response.template_name}</div>
                    <div className="text-xs text-gray-500">{response.template_id.substring(0, 8)}...</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{response.opportunity_type}</div>
                    <div className="text-xs text-gray-500">{response.opportunity_subtype}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-lg font-bold ${getScoreColor(response.score_percentage)}`}>
                      {response.score_percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {response.total_score.toFixed(1)} / {response.max_possible_score.toFixed(1)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {response.completion_percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {response.answered_questions} / {response.total_questions}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(response.submitted_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handleViewResponse(response.response_id)}
                        className="text-opex-cyan hover:text-opex-cyan/80 p-2 rounded hover:bg-gray-100"
                        title="View Details"
                      >
                        <Eye size={18} />
                      </button>
                      <button
                        onClick={() => handleDeleteResponse(response.response_id)}
                        className="text-red-600 hover:text-red-800 p-2 rounded hover:bg-gray-100"
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow-sm px-6 py-4">
          <div className="text-sm text-gray-600">
            Page {pagination.page} of {pagination.total_pages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page === pagination.total_pages}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
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

export default ResponseListPage;
