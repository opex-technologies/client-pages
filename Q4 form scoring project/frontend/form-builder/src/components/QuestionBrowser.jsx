/**
 * Question Browser Component
 * Browse and search questions from the database
 */

import { useEffect, useState } from 'react';
import { Search, Plus, Filter, Loader, Database } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const QuestionBrowser = ({ onAddQuestion, selectedQuestionIds = [], opportunitySubtype }) => {
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    fetchQuestions();
  }, [opportunitySubtype, filterCategory]);

  const fetchQuestions = async (reset = true) => {
    setIsLoading(true);
    try {
      const params = {
        page_size: 20,
        page: reset ? 1 : page,
      };

      if (opportunitySubtype) {
        params.opportunity_subtype = opportunitySubtype;
      }
      if (filterCategory !== 'all') {
        params.category = filterCategory;
      }

      const response = await formBuilderAPI.getQuestions(params);

      if (response.data.success) {
        const newQuestions = response.data.data.items || [];
        if (reset) {
          setQuestions(newQuestions);
          setPage(1);
        } else {
          setQuestions([...questions, ...newQuestions]);
        }
        setHasMore(newQuestions.length === 20);
      }
    } catch (error) {
      console.error('Failed to fetch questions:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadMore = () => {
    setPage(page + 1);
    fetchQuestions(false);
  };

  const filteredQuestions = questions.filter(q =>
    q.question_text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const QuestionCard = ({ question }) => {
    const isSelected = selectedQuestionIds.includes(question.question_id);

    return (
      <div
        className={`p-4 rounded-lg border-2 transition-all ${
          isSelected
            ? 'border-opex-cyan bg-cyan-50'
            : 'border-gray-200 hover:border-opex-navy hover:shadow-md'
        }`}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded mb-2">
              {question.category}
            </span>
            <p className="text-sm text-gray-900 font-medium line-clamp-3">
              {question.question_text}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span className="px-2 py-1 bg-gray-100 rounded">{question.input_type}</span>
            <span>Weight: {question.default_weight || 'Info'}</span>
          </div>
          <button
            onClick={() => onAddQuestion(question)}
            disabled={isSelected}
            className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              isSelected
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-opex-navy text-white hover:bg-opex-navy/90'
            }`}
          >
            <Plus size={16} />
            <span>{isSelected ? 'Added' : 'Add'}</span>
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
          <Database size={24} />
          <span>Question Database</span>
        </h2>
        <span className="text-sm text-gray-600">{filteredQuestions.length} questions</span>
      </div>

      {/* Search and Filter */}
      <div className="space-y-3 mb-4">
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

        <select
          value={filterCategory}
          onChange={(e) => {
            setFilterCategory(e.target.value);
            fetchQuestions(true);
          }}
          className="input-field"
        >
          <option value="all">All Categories</option>
          <option value="Overview">Overview</option>
          <option value="Help Desk">Help Desk</option>
          <option value="Telephony">Telephony</option>
          <option value="Network">Network</option>
          <option value="Security">Security</option>
          <option value="Cloud">Cloud</option>
          <option value="Data Center">Data Center</option>
          <option value="Professional Services">Professional Services</option>
          <option value="Expense Management">Expense Management</option>
        </select>
      </div>

      {/* Questions List */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
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
                className="w-full py-2 text-sm text-opex-navy hover:bg-gray-50 rounded-lg transition-colors"
              >
                Load More Questions
              </button>
            )}

            {isLoading && (
              <div className="text-center py-4">
                <Loader className="animate-spin h-6 w-6 text-opex-navy mx-auto" />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <Filter size={48} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600">No questions found</p>
            <p className="text-sm text-gray-500 mt-1">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuestionBrowser;
