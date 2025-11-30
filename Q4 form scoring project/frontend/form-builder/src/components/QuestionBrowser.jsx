/**
 * Question Browser Component
 * Browse and search questions from the database
 */

import { useEffect, useState } from 'react';
import { Search, Plus, Filter, Loader, Database, X } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const QuestionBrowser = ({ onAddQuestion, selectedQuestionIds = [], opportunitySubtype }) => {
  const [questions, setQuestions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoriesLoaded, setCategoriesLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Load available categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        // Fetch a large sample to get all unique categories
        const response = await formBuilderAPI.getQuestions({ page_size: 200 });
        if (response.data.success) {
          const allQuestions = response.data.data.items || [];
          const uniqueCategories = [...new Set(allQuestions.map(q => q.category))].sort();
          setCategories(uniqueCategories);
        }
      } catch (error) {
        console.error('Failed to load categories:', error);
      } finally {
        setCategoriesLoaded(true);
      }
    };
    loadCategories();
  }, []);

  // Fetch questions when filters change (with debounce for search only)
  useEffect(() => {
    // Don't fetch until categories are loaded
    if (!categoriesLoaded) return;

    // Use AbortController to cancel stale requests
    const abortController = new AbortController();

    // Only debounce search term changes, not filter/subtype changes
    const debounceDelay = 300;
    const timeoutId = setTimeout(() => {
      const fetchQuestions = async () => {
        setIsLoading(true);
        try {
          const params = {
            page_size: 20,
            page: 1,
          };

          if (opportunitySubtype) {
            params.opportunity_subtype = opportunitySubtype;
          }
          if (filterCategory !== 'all') {
            params.category = filterCategory;
          }
          if (searchTerm.trim()) {
            params.search = searchTerm.trim();
          }

          const response = await formBuilderAPI.getQuestions(params);

          // Only update state if request wasn't aborted
          if (!abortController.signal.aborted) {
            if (response.data.success) {
              const newQuestions = response.data.data.items || [];
              setQuestions(newQuestions);
              setPage(1);
              setHasMore(newQuestions.length === 20);
            }
          }
        } catch (error) {
          // Ignore abort errors
          if (error.name === 'AbortError' || abortController.signal.aborted) {
            return;
          }
          console.error('Failed to fetch questions:', error);
          toast.error(getErrorMessage(error));
          if (!abortController.signal.aborted) {
            setQuestions([]);
          }
        } finally {
          if (!abortController.signal.aborted) {
            setIsLoading(false);
          }
        }
      };

      fetchQuestions();
    }, debounceDelay);

    return () => {
      clearTimeout(timeoutId);
      abortController.abort();
    };
  }, [categoriesLoaded, opportunitySubtype, filterCategory, searchTerm]);

  const handleLoadMore = async () => {
    setIsLoading(true);
    try {
      const nextPage = page + 1;
      const params = {
        page_size: 20,
        page: nextPage,
      };

      if (opportunitySubtype) {
        params.opportunity_subtype = opportunitySubtype;
      }
      if (filterCategory !== 'all') {
        params.category = filterCategory;
      }
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }

      const response = await formBuilderAPI.getQuestions(params);

      if (response.data.success) {
        const newQuestions = response.data.data.items || [];
        setQuestions(prevQuestions => [...prevQuestions, ...newQuestions]);
        setPage(nextPage);
        setHasMore(newQuestions.length === 20);
      }
    } catch (error) {
      console.error('Failed to load more questions:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  // Remove already selected questions from display
  // (Search filtering is now done server-side)
  const filteredQuestions = questions
    .filter(q => !selectedQuestionIds.includes(q.question_id));

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
          {isLoading && questions.length === 0 ? (
            <span className="text-gray-400">Loading...</span>
          ) : (
            <span className="text-gray-600 font-medium">
              {filteredQuestions.length} question{filteredQuestions.length !== 1 ? 's' : ''}
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
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
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
        {isLoading && questions.length === 0 ? (
          <div className="text-center py-8">
            <Loader className="animate-spin h-8 w-8 text-opex-navy mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Loading questions...</p>
          </div>
        ) : filteredQuestions.length > 0 ? (
          <>
            {filteredQuestions.map((question) => (
              <QuestionCard key={question.question_id} question={question} />
            ))}

            {hasMore && !isLoading && (
              <button
                onClick={handleLoadMore}
                className="w-full py-3 text-sm font-medium text-opex-navy bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
              >
                Load More Questions ({questions.length} shown)
              </button>
            )}

            {isLoading && questions.length > 0 && (
              <div className="text-center py-4">
                <Loader className="animate-spin h-6 w-6 text-opex-navy mx-auto mb-2" />
                <p className="text-xs text-gray-500">Loading more...</p>
              </div>
            )}
          </>
        ) : !isLoading ? (
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
        ) : null}
      </div>
    </div>
  );
};

export default QuestionBrowser;
