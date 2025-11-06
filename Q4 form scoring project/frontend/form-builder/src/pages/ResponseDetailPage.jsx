/**
 * Response Detail Page
 * Shows detailed view of a single response with all answers and scoring breakdown
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Trash2, CheckCircle, XCircle, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import { responseScorerAPI, getErrorMessage } from '../services/responseScorerApi';

const ResponseDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResponse();
  }, [id]);

  const loadResponse = async () => {
    try {
      setLoading(true);
      const result = await responseScorerAPI.getResponse(id);
      setResponse(result.data.data);
    } catch (error) {
      toast.error(getErrorMessage(error));
      navigate('/responses');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this response? This action cannot be undone.')) {
      return;
    }

    try {
      await responseScorerAPI.deleteResponse(id);
      toast.success('Response deleted successfully');
      navigate('/responses');
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleExportPDF = () => {
    toast.info('PDF export coming soon');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600 bg-green-50';
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getAnswerIcon = (answer) => {
    if (!answer.answer_value || answer.answer_value.trim() === '') {
      return <XCircle className="text-gray-400" size={20} />;
    }
    if (answer.points_possible === 0) {
      return <Info className="text-blue-500" size={20} />;
    }
    if (answer.points_earned > 0) {
      return <CheckCircle className="text-green-500" size={20} />;
    }
    return <XCircle className="text-red-500" size={20} />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-opex-cyan mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading response...</p>
        </div>
      </div>
    );
  }

  if (!response) {
    return null;
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Back Button */}
      <button
        onClick={() => navigate('/responses')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={20} />
        Back to Responses
      </button>

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-opex-navy mb-2">
              {response.template_name}
            </h1>
            <div className="space-y-1 text-sm text-gray-600">
              <p>
                <span className="font-medium">Response ID:</span> {response.response_id}
              </p>
              <p>
                <span className="font-medium">Submitted:</span> {formatDate(response.submitted_at)}
              </p>
              {response.submitter_name && (
                <p>
                  <span className="font-medium">Submitter:</span> {response.submitter_name}
                </p>
              )}
              {response.submitter_email && (
                <p>
                  <span className="font-medium">Email:</span> {response.submitter_email}
                </p>
              )}
              <p>
                <span className="font-medium">Type:</span> {response.opportunity_type} / {response.opportunity_subtype}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleExportPDF}
              className="px-4 py-2 bg-opex-cyan text-white rounded-lg hover:bg-opex-cyan/90 flex items-center gap-2"
            >
              <Download size={20} />
              Export PDF
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
            >
              <Trash2 size={20} />
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Score Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`bg-white rounded-lg shadow-sm p-6 border-2 ${getScoreColor(response.score_percentage)}`}>
          <h3 className="text-sm font-medium mb-1">Overall Score</h3>
          <p className="text-4xl font-bold">{response.score_percentage.toFixed(1)}%</p>
          <p className="text-xs mt-1 opacity-75">
            {response.total_score.toFixed(1)} / {response.max_possible_score.toFixed(1)} points
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-1">Completion Rate</h3>
          <p className="text-4xl font-bold text-opex-navy">{response.completion_percentage.toFixed(1)}%</p>
          <p className="text-xs text-gray-600 mt-1">
            {response.answered_questions} / {response.total_questions} questions
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-1">Questions Answered</h3>
          <p className="text-4xl font-bold text-opex-navy">{response.answered_questions}</p>
          <p className="text-xs text-gray-600 mt-1">
            of {response.total_questions} total
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-1">Questions Skipped</h3>
          <p className="text-4xl font-bold text-gray-400">
            {response.total_questions - response.answered_questions}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            unanswered
          </p>
        </div>
      </div>

      {/* Answer Details */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-opex-navy">Answer Details</h2>
          <p className="text-sm text-gray-600 mt-1">
            Showing all {response.answers?.length || 0} questions
          </p>
        </div>

        <div className="divide-y divide-gray-200">
          {response.answers && response.answers.length > 0 ? (
            response.answers.map((answer, index) => (
              <div key={answer.answer_id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-1">
                    {getAnswerIcon(answer)}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-2">
                          {index + 1}. {answer.question_text}
                        </h3>

                        {answer.answer_value && answer.answer_value.trim() !== '' ? (
                          <div className="bg-gray-50 rounded-lg p-3 mb-3">
                            <p className="text-gray-800">{answer.answer_value}</p>
                          </div>
                        ) : (
                          <div className="bg-gray-100 rounded-lg p-3 mb-3">
                            <p className="text-gray-500 italic">No answer provided</p>
                          </div>
                        )}

                        <div className="text-xs text-gray-500">
                          Question ID: {answer.question_id}
                        </div>
                      </div>

                      <div className="flex-shrink-0 text-right">
                        {answer.points_possible > 0 ? (
                          <>
                            <div className="text-2xl font-bold text-opex-navy">
                              {answer.points_earned.toFixed(1)}
                            </div>
                            <div className="text-xs text-gray-600">
                              / {answer.points_possible.toFixed(1)} pts
                            </div>
                            {answer.points_earned > 0 ? (
                              <div className="text-xs text-green-600 font-medium mt-1">
                                Points Earned
                              </div>
                            ) : (
                              <div className="text-xs text-red-600 font-medium mt-1">
                                No Points
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="text-xs text-blue-600 font-medium">
                            Info Only
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center text-gray-500">
              No answers recorded for this response
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Legend</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-green-500" size={18} />
            <span className="text-gray-700">Answer provided with points</span>
          </div>
          <div className="flex items-center gap-2">
            <Info className="text-blue-500" size={18} />
            <span className="text-gray-700">Informational question (no points)</span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="text-red-500" size={18} />
            <span className="text-gray-700">Question not answered</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponseDetailPage;
