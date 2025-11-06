/**
 * Dashboard Page
 * Shows overview metrics and quick actions
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Database, Upload, Plus, TrendingUp } from 'lucide-react';
import { formBuilderAPI } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalTemplates: 0,
    publishedTemplates: 0,
    draftTemplates: 0,
    totalQuestions: 1041, // Static for now
  });
  const [recentTemplates, setRecentTemplates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      // Fetch templates for stats
      const response = await formBuilderAPI.getTemplates({ page_size: 100 });

      if (response.data.success) {
        const templates = response.data.data.items || [];

        setStats({
          totalTemplates: templates.length,
          publishedTemplates: templates.filter(t => t.status === 'published').length,
          draftTemplates: templates.filter(t => t.status === 'draft').length,
          totalQuestions: 1041,
        });

        // Get 5 most recent templates
        setRecentTemplates(templates.slice(0, 5));
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="card hover:shadow-lg transition-shadow">
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
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome to the Form Builder</p>
        </div>
        <button
          onClick={() => navigate('/templates/new')}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus size={20} />
          <span>Create New Template</span>
        </button>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-24 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Templates"
            value={stats.totalTemplates}
            icon={FileText}
            color="bg-opex-navy"
          />
          <StatCard
            title="Published Forms"
            value={stats.publishedTemplates}
            icon={Upload}
            color="bg-green-600"
          />
          <StatCard
            title="Draft Templates"
            value={stats.draftTemplates}
            icon={FileText}
            color="bg-yellow-600"
          />
          <StatCard
            title="Questions Available"
            value={stats.totalQuestions}
            icon={Database}
            color="bg-opex-cyan"
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/templates/new')}
              className="w-full flex items-center justify-between p-4 rounded-lg border-2 border-gray-200 hover:border-opex-navy hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-opex-navy rounded-lg">
                  <Plus size={20} className="text-white" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-gray-900">Create New Template</p>
                  <p className="text-sm text-gray-600">Build a new form from scratch</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => navigate('/templates')}
              className="w-full flex items-center justify-between p-4 rounded-lg border-2 border-gray-200 hover:border-opex-cyan hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-opex-cyan rounded-lg">
                  <FileText size={20} className="text-white" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-gray-900">Browse Templates</p>
                  <p className="text-sm text-gray-600">View and manage existing forms</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => navigate('/questions')}
              className="w-full flex items-center justify-between p-4 rounded-lg border-2 border-gray-200 hover:border-green-600 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-600 rounded-lg">
                  <Database size={20} className="text-white" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-gray-900">Question Database</p>
                  <p className="text-sm text-gray-600">Browse 1,041 available questions</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Templates</h2>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded animate-pulse"></div>
              ))}
            </div>
          ) : recentTemplates.length > 0 ? (
            <div className="space-y-3">
              {recentTemplates.map((template) => (
                <button
                  key={template.template_id}
                  onClick={() => navigate(`/templates/${template.template_id}/edit`)}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-opex-navy hover:bg-gray-50 transition-colors text-left"
                >
                  <div>
                    <p className="font-medium text-gray-900">{template.template_name}</p>
                    <p className="text-sm text-gray-600">
                      {template.opportunity_type} - {template.opportunity_subtype}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      template.status === 'published'
                        ? 'bg-green-100 text-green-800'
                        : template.status === 'draft'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {template.status}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText size={48} className="mx-auto mb-3 opacity-50" />
              <p>No templates yet</p>
              <button
                onClick={() => navigate('/templates/new')}
                className="mt-4 text-opex-cyan hover:underline"
              >
                Create your first template
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
