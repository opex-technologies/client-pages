/**
 * Question Database Page
 * Browse and search all available questions
 */

import { useEffect, useState } from 'react';
import { Search, Filter, Database, TrendingUp, Download, Info } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const QuestionDatabasePage = () => {
  const [questions, setQuestions] = useState([]);
  const [filteredQuestions, setFilteredQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterSubtype, setFilterSubtype] = useState('all');
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Statistics
  const [stats, setStats] = useState({
    total: 0,
    byCategory: {},
    byType: {},
    byInputType: {},
  });

  useEffect(() => {
    fetchQuestions();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [questions, searchTerm, filterCategory, filterType, filterSubtype]);

  const fetchQuestions = async (loadMore = false) => {
    setIsLoading(true);
    try {
      const params = {
        page_size: 100,
        page: loadMore ? page + 1 : 1,
      };

      const response = await formBuilderAPI.getQuestions(params);

      if (response.data.success) {
        const newQuestions = response.data.data.items || [];

        if (loadMore) {
          setQuestions([...questions, ...newQuestions]);
          setPage(page + 1);
        } else {
          setQuestions(newQuestions);
          calculateStats(newQuestions);
        }

        setHasMore(newQuestions.length === 100);
      }
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = (questionList) => {
    const byCategory = {};
    const byType = {};
    const byInputType = {};

    questionList.forEach(q => {
      // By category
      byCategory[q.category] = (byCategory[q.category] || 0) + 1;

      // By opportunity type
      byType[q.opportunity_type] = (byType[q.opportunity_type] || 0) + 1;

      // By input type
      byInputType[q.input_type] = (byInputType[q.input_type] || 0) + 1;
    });

    setStats({
      total: questionList.length,
      byCategory,
      byType,
      byInputType,
    });
  };

  const applyFilters = () => {
    let filtered = [...questions];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(q =>
        q.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Category filter
    if (filterCategory !== 'all') {
      filtered = filtered.filter(q => q.category === filterCategory);
    }

    // Type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(q => q.opportunity_type === filterType);
    }

    // Subtype filter
    if (filterSubtype !== 'all') {
      filtered = filtered.filter(q => q.opportunity_subtype === filterSubtype);
    }

    setFilteredQuestions(filtered);
  };

  const handleExportCSV = () => {
    const csv = [
      ['Question ID', 'Question Text', 'Category', 'Opportunity Type', 'Opportunity Subtype', 'Input Type', 'Default Weight'].join(','),
      ...filteredQuestions.map(q => [
        q.question_id,
        `"${q.question_text.replace(/"/g, '""')}"`,
        q.category,
        q.opportunity_type,
        q.opportunity_subtype,
        q.input_type,
        q.default_weight || 'Info',
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `questions-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Questions exported to CSV');
  };

  const QuestionCard = ({ question }) => (
    <div
      onClick={() => setSelectedQuestion(question)}
      className="p-4 rounded-lg border-2 border-gray-200 hover:border-opex-navy hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
          {question.category}
        </span>
        <span className="text-xs text-gray-500">{question.input_type}</span>
      </div>

      <p className="text-sm text-gray-900 font-medium mb-3 line-clamp-3">
        {question.question_text}
      </p>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-gray-500">
          <span className="px-2 py-1 bg-gray-100 rounded">{question.opportunity_type}</span>
          <span className="px-2 py-1 bg-gray-100 rounded">{question.opportunity_subtype}</span>
        </div>
        <span className="font-medium text-opex-navy">
          {question.default_weight || 'Info'}
        </span>
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
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Question Database</h1>
          <p className="text-gray-600 mt-1">
            Browse and search {stats.total.toLocaleString()} available questions
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          disabled={filteredQuestions.length === 0}
          className="btn-secondary flex items-center space-x-2"
        >
          <Download size={20} />
          <span>Export CSV ({filteredQuestions.length})</span>
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Questions"
          value={stats.total.toLocaleString()}
          icon={Database}
          color="bg-opex-navy"
        />
        <StatCard
          title="Categories"
          value={Object.keys(stats.byCategory).length}
          icon={Filter}
          color="bg-opex-cyan"
        />
        <StatCard
          title="Opportunity Types"
          value={Object.keys(stats.byType).length}
          icon={TrendingUp}
          color="bg-green-600"
        />
        <StatCard
          title="Input Types"
          value={Object.keys(stats.byInputType).length}
          icon={Info}
          color="bg-purple-600"
        />
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-1">
            <label className="label">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search questions..."
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <label className="label">Category</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="input-field"
            >
              <option value="all">All Categories ({stats.total})</option>
              {Object.entries(stats.byCategory)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([category, count]) => (
                  <option key={category} value={category}>
                    {category} ({count})
                  </option>
                ))}
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
              {Object.keys(stats.byType).sort().map((type) => (
                <option key={type} value={type}>
                  {type} ({stats.byType[type]})
                </option>
              ))}
            </select>
          </div>

          {/* Subtype Filter */}
          <div>
            <label className="label">Opportunity Subtype</label>
            <input
              type="text"
              value={filterSubtype}
              onChange={(e) => setFilterSubtype(e.target.value)}
              placeholder="Filter by subtype..."
              className="input-field"
            />
          </div>
        </div>

        {/* Active Filters Summary */}
        {(searchTerm || filterCategory !== 'all' || filterType !== 'all' || filterSubtype !== 'all') && (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {filteredQuestions.length} of {stats.total} questions
            </p>
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterCategory('all');
                setFilterType('all');
                setFilterSubtype('all');
              }}
              className="text-sm text-opex-cyan hover:underline"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Questions Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredQuestions.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredQuestions.map((question) => (
              <QuestionCard key={question.question_id} question={question} />
            ))}
          </div>

          {hasMore && (
            <div className="text-center mt-6">
              <button
                onClick={() => fetchQuestions(true)}
                className="btn-secondary"
              >
                Load More Questions
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-16">
          <Database size={64} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No questions found</h3>
          <p className="text-gray-500 mb-6">Try adjusting your search or filters</p>
          <button
            onClick={() => {
              setSearchTerm('');
              setFilterCategory('all');
              setFilterType('all');
              setFilterSubtype('all');
            }}
            className="btn-primary"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Question Detail Modal */}
      {selectedQuestion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Question Details</h2>
                <button
                  onClick={() => setSelectedQuestion(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Question ID</label>
                  <p className="text-sm font-mono bg-gray-100 p-2 rounded">{selectedQuestion.question_id}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Question Text</label>
                  <p className="text-gray-900">{selectedQuestion.question_text}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Category</label>
                    <p className="text-gray-900">{selectedQuestion.category}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Input Type</label>
                    <p className="text-gray-900">{selectedQuestion.input_type}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Opportunity Type</label>
                    <p className="text-gray-900">{selectedQuestion.opportunity_type}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Opportunity Subtype</label>
                    <p className="text-gray-900">{selectedQuestion.opportunity_subtype}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Default Weight</label>
                    <p className="text-gray-900">{selectedQuestion.default_weight || 'Info (No Score)'}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-600">Status</label>
                    <p className="text-gray-900">{selectedQuestion.is_active ? 'Active' : 'Inactive'}</p>
                  </div>
                </div>

                {selectedQuestion.help_text && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Help Text</label>
                    <p className="text-gray-900">{selectedQuestion.help_text}</p>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedQuestion(null)}
                  className="btn-primary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuestionDatabasePage;
