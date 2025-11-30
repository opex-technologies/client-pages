/**
 * Question Database Page
 * Browse, search, and manage all available questions
 * Includes full CRUD operations: Create, Read, Update, Delete
 */

import { useEffect, useState } from 'react';
import { Search, Filter, Database, TrendingUp, Download, Info, Plus, Edit, Trash2, X, Save } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';
import ConfirmDialog from '../components/ConfirmDialog';

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

  // Editor state
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

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

  // Add Escape key handlers for modals
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        if (isEditorOpen) {
          setIsEditorOpen(false);
          setEditingQuestion(null);
        } else if (selectedQuestion) {
          setSelectedQuestion(null);
        }
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isEditorOpen, selectedQuestion]);

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
      byCategory[q.category] = (byCategory[q.category] || 0) + 1;
      byType[q.opportunity_type] = (byType[q.opportunity_type] || 0) + 1;
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

    if (searchTerm) {
      filtered = filtered.filter(q =>
        q.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
        q.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter(q => q.category === filterCategory);
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(q => q.opportunity_type === filterType);
    }

    if (filterSubtype !== 'all') {
      filtered = filtered.filter(q => q.opportunity_subtype === filterSubtype);
    }

    setFilteredQuestions(filtered);
  };

  const handleCreateQuestion = () => {
    setEditingQuestion({
      question_text: '',
      category: '',
      opportunity_type: 'All',
      opportunity_subtype: 'All',
      input_type: 'textarea',
      default_weight: '',
      help_text: '',
    });
    setIsEditorOpen(true);
  };

  const handleEditQuestion = (question) => {
    setEditingQuestion({ ...question });
    setIsEditorOpen(true);
    setSelectedQuestion(null);
  };

  const handleSaveQuestion = async (questionData) => {
    setIsSaving(true);
    try {
      if (editingQuestion.question_id) {
        // Update existing question
        await formBuilderAPI.updateQuestion(editingQuestion.question_id, questionData);
        toast.success('Question updated successfully (may take up to 90 minutes to appear)');
      } else {
        // Create new question
        await formBuilderAPI.createQuestion(questionData);
        toast.success('Question created successfully');
      }

      setIsEditorOpen(false);
      setEditingQuestion(null);
      // Refresh questions after a short delay
      setTimeout(() => fetchQuestions(), 1000);
    } catch (error) {
      console.error('Failed to save question:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Question',
      message: 'Are you sure you want to delete this question? This action cannot be undone.',
      onConfirm: async () => {
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });
        try {
          await formBuilderAPI.deleteQuestion(questionId);
          toast.success('Question deleted successfully (may take up to 90 minutes to take effect)');
          setSelectedQuestion(null);
          setTimeout(() => fetchQuestions(), 1000);
        } catch (error) {
          console.error('Failed to delete question:', error);
          toast.error(getErrorMessage(error));
        }
      }
    });
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

  // Sub-components

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

  const QuestionEditorModal = () => {
    const [formData, setFormData] = useState(editingQuestion || {});
    const [errors, setErrors] = useState({});

    const validate = () => {
      const newErrors = {};

      if (!formData.question_text?.trim()) {
        newErrors.question_text = 'Question text is required';
      } else if (formData.question_text.length > 1000) {
        newErrors.question_text = 'Question text must be 1000 characters or less';
      }

      if (!formData.category?.trim()) {
        newErrors.category = 'Category is required';
      }

      if (!formData.input_type) {
        newErrors.input_type = 'Input type is required';
      }

      if (formData.default_weight && formData.default_weight !== 'Info' && formData.default_weight !== 'info') {
        const weight = Number(formData.default_weight);
        if (isNaN(weight) || weight < 0 || weight > 100) {
          newErrors.default_weight = 'Weight must be between 0 and 100, or "Info"';
        }
      }

      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
      e.preventDefault();
      if (validate()) {
        handleSaveQuestion(formData);
      }
    };

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmit} className="p-6">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingQuestion?.question_id ? 'Edit Question' : 'Create New Question'}
              </h2>
              <button
                type="button"
                onClick={() => {
                  setIsEditorOpen(false);
                  setEditingQuestion(null);
                }}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Close editor"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-4">
              {/* Question Text */}
              <div>
                <label className="label required">Question Text</label>
                <textarea
                  value={formData.question_text || ''}
                  onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
                  rows={3}
                  className={`input-field ${errors.question_text ? 'border-red-500' : ''}`}
                  placeholder="Enter the question text..."
                />
                {errors.question_text && (
                  <p className="text-red-500 text-sm mt-1">{errors.question_text}</p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  {formData.question_text?.length || 0} / 1000 characters
                </p>
              </div>

              {/* Category and Input Type */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label required">Category</label>
                  <input
                    type="text"
                    value={formData.category || ''}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className={`input-field ${errors.category ? 'border-red-500' : ''}`}
                    placeholder="e.g., Customer"
                  />
                  {errors.category && (
                    <p className="text-red-500 text-sm mt-1">{errors.category}</p>
                  )}
                </div>

                <div>
                  <label className="label required">Input Type</label>
                  <select
                    value={formData.input_type || 'textarea'}
                    onChange={(e) => setFormData({ ...formData, input_type: e.target.value })}
                    className={`input-field ${errors.input_type ? 'border-red-500' : ''}`}
                  >
                    <option value="text">Text (single line)</option>
                    <option value="textarea">Textarea (multiple lines)</option>
                    <option value="number">Number</option>
                    <option value="radio">Radio buttons</option>
                    <option value="select">Dropdown select</option>
                    <option value="checkbox">Checkboxes</option>
                  </select>
                  {errors.input_type && (
                    <p className="text-red-500 text-sm mt-1">{errors.input_type}</p>
                  )}
                </div>
              </div>

              {/* Opportunity Type and Subtype */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Opportunity Type</label>
                  <input
                    type="text"
                    value={formData.opportunity_type || 'All'}
                    onChange={(e) => setFormData({ ...formData, opportunity_type: e.target.value })}
                    className="input-field"
                    placeholder="All"
                  />
                  <p className="text-sm text-gray-500 mt-1">Leave as "All" for universal questions</p>
                </div>

                <div>
                  <label className="label">Opportunity Subtype</label>
                  <input
                    type="text"
                    value={formData.opportunity_subtype || 'All'}
                    onChange={(e) => setFormData({ ...formData, opportunity_subtype: e.target.value })}
                    className="input-field"
                    placeholder="All"
                  />
                  <p className="text-sm text-gray-500 mt-1">Leave as "All" for universal questions</p>
                </div>
              </div>

              {/* Default Weight */}
              <div>
                <label className="label">Default Weight</label>
                <input
                  type="text"
                  value={formData.default_weight || ''}
                  onChange={(e) => setFormData({ ...formData, default_weight: e.target.value })}
                  className={`input-field ${errors.default_weight ? 'border-red-500' : ''}`}
                  placeholder='Enter 0-100 or "Info" for non-scored questions'
                />
                {errors.default_weight && (
                  <p className="text-red-500 text-sm mt-1">{errors.default_weight}</p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  0-100 for scored questions, or "Info" for informational questions
                </p>
              </div>

              {/* Help Text */}
              <div>
                <label className="label">Help Text (Optional)</label>
                <textarea
                  value={formData.help_text || ''}
                  onChange={(e) => setFormData({ ...formData, help_text: e.target.value })}
                  rows={2}
                  className="input-field"
                  placeholder="Additional context or instructions for this question..."
                />
              </div>
            </div>

            {/* BigQuery Warning */}
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> Due to BigQuery streaming buffer limitations, updates may take up to 90 minutes to appear.
                Created questions appear immediately.
              </p>
            </div>

            {/* Actions */}
            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setIsEditorOpen(false);
                  setEditingQuestion(null);
                }}
                className="btn-secondary"
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary flex items-center space-x-2"
                disabled={isSaving}
              >
                <Save size={20} />
                <span>{isSaving ? 'Saving...' : 'Save Question'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Question Database</h1>
          <p className="text-gray-600 mt-1">
            Browse and manage {stats.total.toLocaleString()} available questions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCreateQuestion}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus size={20} />
            <span>Create Question</span>
          </button>
          <button
            onClick={handleExportCSV}
            disabled={filteredQuestions.length === 0}
            className="btn-secondary flex items-center space-x-2"
          >
            <Download size={20} />
            <span>Export ({filteredQuestions.length})</span>
          </button>
        </div>
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
                  aria-label="Close question details"
                >
                  <X size={24} />
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

              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => handleDeleteQuestion(selectedQuestion.question_id)}
                  className="btn-secondary text-red-600 hover:bg-red-50 flex items-center space-x-2"
                >
                  <Trash2 size={20} />
                  <span>Delete</span>
                </button>
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleEditQuestion(selectedQuestion)}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Edit size={20} />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => setSelectedQuestion(null)}
                    className="btn-secondary"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Editor Modal */}
      {isEditorOpen && <QuestionEditorModal />}

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

export default QuestionDatabasePage;
