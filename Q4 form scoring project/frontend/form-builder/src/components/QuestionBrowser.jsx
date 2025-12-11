/**
 * Question Browser Component
 * Browse and search questions from the database
 * Loads all questions upfront and filters client-side for instant filtering
 */

import { useEffect, useState, useMemo } from 'react';
import { Search, Plus, Filter, Loader, Database, X } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const QuestionBrowser = ({ onAddQuestion, selectedQuestionIds = [] }) => {
  const [allQuestions, setAllQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');

  // Load all questions on mount
  useEffect(() => {
    const loadAllQuestions = async () => {
      setIsLoading(true);
      try {
        const response = await formBuilderAPI.getQuestions({ page_size: 5000 });
        if (response.data.success) {
          setAllQuestions(response.data.data.items || []);
        }
      } catch (error) {
        console.error('Failed to load questions:', error);
        toast.error(getErrorMessage(error));
      } finally {
        setIsLoading(false);
      }
    };
    loadAllQuestions();
  }, []);

  // Extract unique categories from loaded questions
  const categories = useMemo(() => {
    const uniqueCategories = [...new Set(allQuestions.map(q => q.category))];
    return uniqueCategories.sort();
  }, [allQuestions]);

  // Filter questions client-side
  const filteredQuestions = useMemo(() => {
    return allQuestions.filter(q => {
      // Exclude already selected questions
      if (selectedQuestionIds.includes(q.question_id)) {
        return false;
      }

      // Filter by category
      if (filterCategory !== 'all' && q.category !== filterCategory) {
        return false;
      }

      // Filter by search term
      if (searchTerm.trim()) {
        const search = searchTerm.toLowerCase();
        const matchesText = q.question_text?.toLowerCase().includes(search);
        const matchesCategory = q.category?.toLowerCase().includes(search);
        if (!matchesText && !matchesCategory) {
          return false;
        }
      }

      return true;
    });
  }, [allQuestions, selectedQuestionIds, filterCategory, searchTerm]);

  const QuestionCard = ({ question }) => {
    const isSelected = selectedQuestionIds.includes(question.question_id);
    const [isExpanded, setIsExpanded] = useState(false);
    const questionText = question.question_text;
    const isTruncated = questionText.length > 100;

    return (
      <div
        className={`p-3 rounded-lg border-2 transition-all ${
          isSelected
            ? 'border-opex-cyan bg-cyan-50'
            : 'border-gray-200 hover:border-opex-navy hover:shadow-sm'
        }`}
      >
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                {question.category}
              </span>
              <span className="text-xs text-gray-500">{question.input_type}</span>
              <span className="text-xs text-gray-500">
                {question.default_weight ? `${question.default_weight} pts` : 'Info'}
              </span>
            </div>
            <p className={`text-sm text-gray-900 ${!isExpanded && isTruncated ? 'line-clamp-2' : ''}`}>
              {questionText}
            </p>
            {isTruncated && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-xs text-opex-navy hover:underline mt-1"
              >
                {isExpanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
          <button
            onClick={() => onAddQuestion(question)}
            disabled={isSelected}
            className={`flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              isSelected
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-opex-navy text-white hover:bg-opex-navy/90 hover:scale-105'
            }`}
            title={isSelected ? 'Already added' : 'Add to template'}
          >
            <Plus size={16} />
            <span className="hidden sm:inline">{isSelected ? 'Added' : 'Add'}</span>
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="card h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <h2 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
          <Database size={24} />
          <span>Question Database</span>
        </h2>
        <div className="text-sm">
          {isLoading ? (
            <span className="text-gray-400">Loading...</span>
          ) : (
            <span className="text-gray-600 font-medium">
              {filteredQuestions.length} of {allQuestions.length} questions
            </span>
          )}
        </div>
      </div>

      {/* Search and Filter */}
      <div className="space-y-3 mb-4 flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search questions by keyword..."
            className="input-field pl-10 pr-10"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              title="Clear search"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="input-field"
        >
          <option value="all">All Categories ({allQuestions.length})</option>
          {categories.map(cat => {
            const count = allQuestions.filter(q => q.category === cat).length;
            return (
              <option key={cat} value={cat}>{cat} ({count})</option>
            );
          })}
        </select>

        {(searchTerm || filterCategory !== 'all') && (
          <button
            onClick={() => {
              setSearchTerm('');
              setFilterCategory('all');
            }}
            className="w-full text-sm text-opex-navy hover:text-opex-navy/80 py-1"
          >
            Clear all filters
          </button>
        )}
      </div>

      {/* Questions List */}
      <div className="flex-1 space-y-3 overflow-y-auto min-h-0 pr-2">
        {isLoading ? (
          <div className="text-center py-8">
            <Loader className="animate-spin h-8 w-8 text-opex-navy mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Loading all questions...</p>
          </div>
        ) : filteredQuestions.length > 0 ? (
          filteredQuestions.map((question) => (
            <QuestionCard key={question.question_id} question={question} />
          ))
        ) : (
          <div className="text-center py-12">
            <Filter size={48} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600 font-medium mb-1">No questions found</p>
            <p className="text-sm text-gray-500 mb-4">
              {searchTerm || filterCategory !== 'all'
                ? 'Try adjusting your search or filters'
                : 'No questions available'}
            </p>
            {(searchTerm || filterCategory !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterCategory('all');
                }}
                className="text-sm text-opex-navy hover:underline"
              >
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuestionBrowser;
