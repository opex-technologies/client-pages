/**
 * Deployment History Page
 * View all deployed templates and their status
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, ExternalLink, Search, Calendar, Upload, CheckCircle, Edit } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const DeploymentHistoryPage = () => {
  const navigate = useNavigate();
  const [deployments, setDeployments] = useState([]);
  const [filteredDeployments, setFilteredDeployments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  // Statistics
  const [stats, setStats] = useState({
    total: 0,
    thisWeek: 0,
    thisMonth: 0,
    byType: {},
  });

  useEffect(() => {
    fetchDeployments();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [deployments, searchTerm, filterStatus]);

  const fetchDeployments = async () => {
    setIsLoading(true);
    try {
      // Fetch all templates and filter for deployed ones
      const response = await formBuilderAPI.getTemplates({ page_size: 100 });

      if (response.data.success) {
        const allTemplates = response.data.data.items || [];

        // Filter for deployed templates
        const deployed = allTemplates
          .filter(t => t.deployed_url && t.deployed_at)
          .map(t => ({
            ...t,
            deployedDate: new Date(t.deployed_at),
          }))
          .sort((a, b) => b.deployedDate - a.deployedDate);

        setDeployments(deployed);
        calculateStats(deployed);
      }
    } catch (error) {
      console.error('Failed to fetch deployments:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = (deploymentList) => {
    const now = new Date();
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const thisWeek = deploymentList.filter(d => d.deployedDate >= oneWeekAgo).length;
    const thisMonth = deploymentList.filter(d => d.deployedDate >= oneMonthAgo).length;

    const byType = {};
    deploymentList.forEach(d => {
      const key = d.opportunity_type;
      byType[key] = (byType[key] || 0) + 1;
    });

    setStats({
      total: deploymentList.length,
      thisWeek,
      thisMonth,
      byType,
    });
  };

  const applyFilters = () => {
    let filtered = [...deployments];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(d =>
        d.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.opportunity_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.opportunity_subtype.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(d => d.status === filterStatus);
    }

    setFilteredDeployments(filtered);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeAgo = (date) => {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + ' years ago';

    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + ' months ago';

    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + ' days ago';

    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + ' hours ago';

    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + ' minutes ago';

    return 'Just now';
  };

  const DeploymentCard = ({ deployment }) => (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 mb-1">
            {deployment.template_name}
          </h3>
          <p className="text-sm text-gray-600">
            {deployment.opportunity_type} • {deployment.opportunity_subtype}
          </p>
        </div>
        <span
          className={`px-3 py-1 text-xs font-medium rounded-full ${
            deployment.status === 'published'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {deployment.status}
        </span>
      </div>

      {deployment.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {deployment.description}
        </p>
      )}

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <Calendar size={16} className="mr-2" />
          <span>Deployed {getTimeAgo(deployment.deployed_at)}</span>
          <span className="mx-2">•</span>
          <span className="text-xs">{formatDate(deployment.deployed_at)}</span>
        </div>

        <div className="flex items-center text-sm text-gray-600">
          <CheckCircle size={16} className="mr-2 text-green-600" />
          <span>{deployment.question_count || 0} questions</span>
        </div>
      </div>

      {deployment.deployed_url && (
        <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium mb-1">Live URL:</p>
          <a
            href={deployment.deployed_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-green-600 hover:underline break-all flex items-center"
          >
            <ExternalLink size={14} className="mr-1 flex-shrink-0" />
            {deployment.deployed_url}
          </a>
        </div>
      )}

      <div className="flex items-center space-x-2">
        <a
          href={deployment.deployed_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 btn-primary text-sm py-2 flex items-center justify-center space-x-2"
        >
          <ExternalLink size={16} />
          <span>View Live Form</span>
        </a>
        <button
          onClick={() => navigate(`/templates/${deployment.template_id}/edit`)}
          className="flex-1 btn-secondary text-sm py-2 flex items-center justify-center space-x-2"
        >
          <Edit size={16} />
          <span>Edit</span>
        </button>
      </div>
    </div>
  );

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={32} className="text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Deployment History</h1>
        <p className="text-gray-600 mt-1">
          View all deployed forms and access their public URLs
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Deployments"
          value={stats.total}
          icon={Upload}
          color="bg-opex-navy"
        />
        <StatCard
          title="This Week"
          value={stats.thisWeek}
          icon={Calendar}
          color="bg-opex-cyan"
        />
        <StatCard
          title="This Month"
          value={stats.thisMonth}
          icon={History}
          color="bg-green-600"
        />
      </div>

      {/* Breakdown by Type */}
      {Object.keys(stats.byType).length > 0 && (
        <div className="card mb-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Deployments by Type</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.byType)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div key={type} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-opex-navy">{count}</p>
                  <p className="text-sm text-gray-600 mt-1">{type}</p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div>
            <label className="label">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search deployments..."
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
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        {(searchTerm || filterStatus !== 'all') && (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {filteredDeployments.length} of {stats.total} deployments
            </p>
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('all');
              }}
              className="text-sm text-opex-cyan hover:underline"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {/* Deployments Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-48 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredDeployments.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDeployments.map((deployment) => (
            <DeploymentCard key={deployment.template_id} deployment={deployment} />
          ))}
        </div>
      ) : deployments.length === 0 ? (
        <div className="text-center py-16">
          <History size={64} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No deployments yet</h3>
          <p className="text-gray-500 mb-6">
            Deploy your first template to see it appear here
          </p>
          <button
            onClick={() => navigate('/templates')}
            className="btn-primary"
          >
            Browse Templates
          </button>
        </div>
      ) : (
        <div className="text-center py-16">
          <History size={64} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No deployments found</h3>
          <p className="text-gray-500 mb-6">Try adjusting your search or filters</p>
          <button
            onClick={() => {
              setSearchTerm('');
              setFilterStatus('all');
            }}
            className="btn-primary"
          >
            Clear Filters
          </button>
        </div>
      )}
    </div>
  );
};

export default DeploymentHistoryPage;
