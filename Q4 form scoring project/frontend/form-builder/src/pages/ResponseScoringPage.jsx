/**
 * Response Scoring Page
 * Side-by-side comparison and manual scoring interface for form responses
 */

import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Save, CheckCircle, XCircle, MinusCircle, Users, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { responseScorerAPI, getErrorMessage } from '../services/responseScorerApi';
import { formBuilderAPI } from '../services/formBuilderApi';

const ResponseScoringPage = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();

  // State
  const [template, setTemplate] = useState(null);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedResponses, setSelectedResponses] = useState([]);
  const [detailedResponses, setDetailedResponses] = useState({});

  // Manual scoring state - tracks edits per response
  const [scoreEdits, setScoreEdits] = useState({});
  const [expandedComments, setExpandedComments] = useState({});

  // Load template and responses
  useEffect(() => {
    loadData();
  }, [templateId]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load template details
      const templateResult = await formBuilderAPI.getTemplate(templateId);
      const templateData = templateResult.data?.data || templateResult.data;
      setTemplate(templateData);

      // Load all responses for this template
      const responsesResult = await responseScorerAPI.getResponses({
        template_id: templateId,
        page_size: 100
      });
      const responsesData = responsesResult.data?.data || responsesResult.data || {};
      const responsesList = responsesData.items || [];
      setResponses(responsesList);

      // Select first 4 responses by default
      const initialSelection = responsesList.slice(0, Math.min(4, responsesList.length)).map(r => r.response_id);
      setSelectedResponses(initialSelection);

    } catch (error) {
      console.error('Error loading data:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // Load detailed response data for selected responses
  useEffect(() => {
    const loadDetails = async () => {
      const newDetails = { ...detailedResponses };

      for (const responseId of selectedResponses) {
        if (!newDetails[responseId]) {
          try {
            const result = await responseScorerAPI.getResponse(responseId);
            const data = result.data?.data || result.data;
            newDetails[responseId] = data;

            // Initialize score edits with current values
            if (data?.answers) {
              const edits = {};
              data.answers.forEach(answer => {
                edits[answer.question_id] = {
                  points_earned: answer.points_earned || 0,
                  points_possible: answer.points_possible || 0,
                  comment: answer.comment || ''
                };
              });
              setScoreEdits(prev => ({
                ...prev,
                [responseId]: edits
              }));
            }
          } catch (error) {
            console.error(`Error loading response ${responseId}:`, error);
          }
        }
      }

      setDetailedResponses(newDetails);
    };

    if (selectedResponses.length > 0) {
      loadDetails();
    }
  }, [selectedResponses]);

  // Get all unique questions from template
  const questions = useMemo(() => {
    if (!template?.questions) return [];
    return template.questions.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
  }, [template]);

  // Toggle response selection
  const toggleResponse = (responseId) => {
    setSelectedResponses(prev => {
      if (prev.includes(responseId)) {
        return prev.filter(id => id !== responseId);
      } else {
        return [...prev, responseId];
      }
    });
  };

  // Get answer for a specific response and question
  const getAnswer = (responseId, questionId) => {
    const response = detailedResponses[responseId];
    if (!response?.answers) return null;
    return response.answers.find(a => a.question_id === questionId);
  };

  // Get current score edit for a response/question
  const getScoreEdit = (responseId, questionId) => {
    return scoreEdits[responseId]?.[questionId] || { points_earned: 0, points_possible: 0, comment: '' };
  };

  // Handle score change
  const handleScoreChange = (responseId, questionId, field, value) => {
    setScoreEdits(prev => ({
      ...prev,
      [responseId]: {
        ...prev[responseId],
        [questionId]: {
          ...prev[responseId]?.[questionId],
          [field]: value
        }
      }
    }));
  };

  // Quick score buttons - Full, Partial, Zero
  const setQuickScore = (responseId, questionId, scoreType) => {
    const question = questions.find(q => q.question_id === questionId);
    const maxPoints = question?.weight || 10;

    let points;
    switch (scoreType) {
      case 'full':
        points = maxPoints;
        break;
      case 'partial':
        points = maxPoints / 2;
        break;
      case 'zero':
      default:
        points = 0;
    }

    handleScoreChange(responseId, questionId, 'points_earned', points);
    handleScoreChange(responseId, questionId, 'points_possible', maxPoints);
  };

  // Calculate total score for a response based on edits
  const calculateTotalScore = (responseId) => {
    const edits = scoreEdits[responseId] || {};
    let totalEarned = 0;
    let totalPossible = 0;

    Object.values(edits).forEach(edit => {
      totalEarned += edit.points_earned || 0;
      totalPossible += edit.points_possible || 0;
    });

    return {
      earned: totalEarned,
      possible: totalPossible,
      percentage: totalPossible > 0 ? (totalEarned / totalPossible * 100) : 0
    };
  };

  // Check if there are unsaved changes
  const hasUnsavedChanges = (responseId) => {
    const response = detailedResponses[responseId];
    const edits = scoreEdits[responseId];
    if (!response?.answers || !edits) return false;

    return response.answers.some(answer => {
      const edit = edits[answer.question_id];
      if (!edit) return false;
      return edit.points_earned !== (answer.points_earned || 0) ||
             edit.comment !== (answer.comment || '');
    });
  };

  // Save scores for a response
  const handleSaveScores = async (responseId) => {
    try {
      setSaving(true);

      const edits = scoreEdits[responseId];
      const response = detailedResponses[responseId];

      if (!edits || !response) {
        toast.error('No scores to save');
        return;
      }

      // Build the score update payload
      const scoreUpdates = Object.entries(edits).map(([questionId, edit]) => ({
        question_id: questionId,
        points_earned: edit.points_earned,
        points_possible: edit.points_possible,
        comment: edit.comment || ''
      }));

      // Call API to update scores
      await responseScorerAPI.updateResponseScores(responseId, {
        question_scores: scoreUpdates
      });

      toast.success('Scores saved successfully');

      // Reload the response to get updated data
      const result = await responseScorerAPI.getResponse(responseId);
      const data = result.data?.data || result.data;
      setDetailedResponses(prev => ({
        ...prev,
        [responseId]: data
      }));

      // Update the responses list with new totals
      const totals = calculateTotalScore(responseId);
      setResponses(prev => prev.map(r =>
        r.response_id === responseId
          ? { ...r, total_score: totals.earned, max_possible_score: totals.possible, score_percentage: totals.percentage }
          : r
      ));

    } catch (error) {
      console.error('Error saving scores:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  // Toggle comment expansion
  const toggleComment = (responseId, questionId) => {
    const key = `${responseId}-${questionId}`;
    setExpandedComments(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Get score color
  const getScoreColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreTextColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Export to CSV
  const handleExport = () => {
    if (selectedResponses.length === 0) {
      toast.error('Select at least one response to export');
      return;
    }

    const headers = ['Question', 'Weight', ...selectedResponses.map(id => {
      const r = responses.find(resp => resp.response_id === id);
      return r?.submitter_name || r?.submitter_email || id.substring(0, 8);
    })];

    const rows = questions.map(q => {
      const row = [q.question_text, q.weight || 0];
      selectedResponses.forEach(responseId => {
        const answer = getAnswer(responseId, q.question_id);
        const edit = getScoreEdit(responseId, q.question_id);
        row.push(`${answer?.answer_value || 'N/A'} (${edit.points_earned}/${edit.points_possible} pts)`);
      });
      return row;
    });

    // Add totals row
    const totalsRow = ['TOTAL SCORE', ''];
    selectedResponses.forEach(responseId => {
      const totals = calculateTotalScore(responseId);
      totalsRow.push(`${totals.earned.toFixed(1)}/${totals.possible.toFixed(1)} (${totals.percentage.toFixed(1)}%)`);
    });
    rows.push(totalsRow);

    const csv = [headers, ...rows].map(row =>
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template?.template_name || 'responses'}_scores_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success('Exported to CSV');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-opex-cyan mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading responses...</p>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Template not found</p>
        <button onClick={() => navigate('/templates')} className="mt-4 text-opex-cyan hover:underline">
          Back to Templates
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/templates')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-opex-navy">Score Responses</h1>
            <p className="text-gray-600">{template.template_name}</p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={selectedResponses.length === 0}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 disabled:opacity-50"
          >
            <Download size={20} />
            Export CSV
          </button>
        </div>
      </div>

      {/* Response Selector */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Users size={20} />
            Select Responses to Score ({selectedResponses.length} selected)
          </h2>
          <div className="flex gap-2 text-sm">
            <button onClick={() => setSelectedResponses(responses.map(r => r.response_id))} className="text-opex-cyan hover:underline">
              Select All
            </button>
            <span className="text-gray-300">|</span>
            <button onClick={() => setSelectedResponses([])} className="text-gray-600 hover:underline">
              Clear
            </button>
          </div>
        </div>

        {responses.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No responses yet for this template</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {responses.map(response => {
              const isSelected = selectedResponses.includes(response.response_id);
              const hasChanges = hasUnsavedChanges(response.response_id);
              return (
                <button
                  key={response.response_id}
                  onClick={() => toggleResponse(response.response_id)}
                  className={`px-3 py-2 rounded-lg border-2 transition-all text-sm relative ${
                    isSelected
                      ? 'border-opex-cyan bg-opex-cyan/10 text-opex-navy'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  {hasChanges && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full" title="Unsaved changes" />
                  )}
                  <div className="font-medium">
                    {response.submitter_name || response.submitter_email || 'Anonymous'}
                  </div>
                  <div className="text-xs opacity-75">
                    {formatDate(response.submitted_at)} • {response.score_percentage?.toFixed(0) || 0}%
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Scoring Instructions */}
      {selectedResponses.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Scoring Instructions</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Click <span className="font-semibold text-green-600">Full</span>, <span className="font-semibold text-yellow-600">Partial</span>, or <span className="font-semibold text-red-600">Zero</span> to quickly assign points</li>
            <li>• Or manually enter a custom point value</li>
            <li>• Add comments to explain your scoring decisions</li>
            <li>• Click <span className="font-semibold">Save Scores</span> to save changes for each response</li>
          </ul>
        </div>
      )}

      {/* Scoring Table */}
      {selectedResponses.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              {/* Header */}
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="text-left p-4 font-semibold text-gray-700 min-w-[300px] sticky left-0 bg-gray-50 z-10">
                    Question
                  </th>
                  {selectedResponses.map(responseId => {
                    const response = responses.find(r => r.response_id === responseId);
                    const hasChanges = hasUnsavedChanges(responseId);
                    return (
                      <th key={responseId} className="p-4 min-w-[280px] text-center">
                        <div className="font-semibold text-gray-900">
                          {response?.submitter_name || 'Anonymous'}
                        </div>
                        <div className="text-xs text-gray-500 font-normal">
                          {response?.submitter_email || 'No email'}
                        </div>
                        <button
                          onClick={() => handleSaveScores(responseId)}
                          disabled={saving || !hasChanges}
                          className={`mt-2 px-3 py-1 text-xs rounded flex items-center gap-1 mx-auto ${
                            hasChanges
                              ? 'bg-opex-cyan text-white hover:bg-opex-cyan/90'
                              : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                          }`}
                        >
                          <Save size={14} />
                          {saving ? 'Saving...' : hasChanges ? 'Save Scores' : 'Saved'}
                        </button>
                      </th>
                    );
                  })}
                </tr>

                {/* Totals row */}
                <tr className="bg-gray-100 border-b">
                  <td className="p-4 font-semibold text-gray-700 sticky left-0 bg-gray-100 z-10">
                    Total Score
                  </td>
                  {selectedResponses.map(responseId => {
                    const totals = calculateTotalScore(responseId);
                    return (
                      <td key={responseId} className="p-4 text-center">
                        <div className={`text-2xl font-bold ${getScoreTextColor(totals.percentage)}`}>
                          {totals.percentage.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">
                          {totals.earned.toFixed(1)} / {totals.possible.toFixed(1)} pts
                        </div>
                        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getScoreColor(totals.percentage)} transition-all`}
                            style={{ width: `${Math.min(100, totals.percentage)}%` }}
                          />
                        </div>
                      </td>
                    );
                  })}
                </tr>
              </thead>

              {/* Question rows */}
              <tbody>
                {questions.map((question, index) => (
                  <tr
                    key={question.question_id}
                    className={`border-b ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                  >
                    <td className={`p-4 sticky left-0 z-10 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      <div className="font-medium text-gray-900 text-sm">
                        {index + 1}. {question.question_text}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Max: {question.weight || 0} pts
                      </div>
                    </td>

                    {selectedResponses.map(responseId => {
                      const answer = getAnswer(responseId, question.question_id);
                      const edit = getScoreEdit(responseId, question.question_id);
                      const hasAnswer = answer?.answer_value && answer.answer_value.trim() !== '';
                      const commentKey = `${responseId}-${question.question_id}`;
                      const isCommentExpanded = expandedComments[commentKey];
                      const maxPoints = question.weight || 10;

                      return (
                        <td key={responseId} className="p-4 align-top">
                          {/* Answer display */}
                          <div className="mb-3">
                            {hasAnswer ? (
                              <div className="text-sm text-gray-800 bg-gray-100 rounded p-2 max-h-24 overflow-y-auto">
                                {answer.answer_value}
                              </div>
                            ) : (
                              <div className="text-gray-400 italic text-sm bg-gray-50 rounded p-2">
                                No answer provided
                              </div>
                            )}
                          </div>

                          {/* Scoring controls */}
                          <div className="space-y-2">
                            {/* Quick score buttons */}
                            <div className="flex gap-1 justify-center">
                              <button
                                onClick={() => setQuickScore(responseId, question.question_id, 'full')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${
                                  edit.points_earned === maxPoints
                                    ? 'bg-green-500 text-white'
                                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                                }`}
                              >
                                Full
                              </button>
                              <button
                                onClick={() => setQuickScore(responseId, question.question_id, 'partial')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${
                                  edit.points_earned === maxPoints / 2
                                    ? 'bg-yellow-500 text-white'
                                    : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                                }`}
                              >
                                Partial
                              </button>
                              <button
                                onClick={() => setQuickScore(responseId, question.question_id, 'zero')}
                                className={`px-2 py-1 text-xs rounded transition-colors ${
                                  edit.points_earned === 0
                                    ? 'bg-red-500 text-white'
                                    : 'bg-red-100 text-red-700 hover:bg-red-200'
                                }`}
                              >
                                Zero
                              </button>
                            </div>

                            {/* Manual point input */}
                            <div className="flex items-center justify-center gap-1 text-sm">
                              <input
                                type="number"
                                min="0"
                                max={maxPoints}
                                step="0.5"
                                value={edit.points_earned}
                                onChange={(e) => handleScoreChange(
                                  responseId,
                                  question.question_id,
                                  'points_earned',
                                  Math.min(maxPoints, Math.max(0, parseFloat(e.target.value) || 0))
                                )}
                                className="w-16 px-2 py-1 border rounded text-center"
                              />
                              <span className="text-gray-500">/ {maxPoints}</span>
                            </div>

                            {/* Comment toggle */}
                            <button
                              onClick={() => toggleComment(responseId, question.question_id)}
                              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mx-auto"
                            >
                              <MessageSquare size={12} />
                              {edit.comment ? 'Edit Comment' : 'Add Comment'}
                              {isCommentExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                            </button>

                            {/* Comment input */}
                            {isCommentExpanded && (
                              <textarea
                                value={edit.comment || ''}
                                onChange={(e) => handleScoreChange(
                                  responseId,
                                  question.question_id,
                                  'comment',
                                  e.target.value
                                )}
                                placeholder="Add scoring notes..."
                                className="w-full px-2 py-1 text-xs border rounded resize-none"
                                rows={2}
                              />
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {selectedResponses.length === 0 && responses.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Select responses to score</h3>
          <p className="text-gray-500">Click on the response cards above to add them to the scoring view</p>
        </div>
      )}
    </div>
  );
};

export default ResponseScoringPage;
