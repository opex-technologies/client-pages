/**
 * Selected Questions List Component
 * Manage selected questions with editing and reordering
 */

import { useState } from 'react';
import { GripVertical, X, Edit2, Check, FileText } from 'lucide-react';

const SelectedQuestionsList = ({ questions, onRemove, onUpdate, onReorder }) => {
  const [editingId, setEditingId] = useState(null);
  const [draggedIndex, setDraggedIndex] = useState(null);

  const handleDragStart = (index) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const reordered = [...questions];
    const draggedItem = reordered[draggedIndex];
    reordered.splice(draggedIndex, 1);
    reordered.splice(index, 0, draggedItem);

    setDraggedIndex(index);
    onReorder(reordered);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const QuestionItem = ({ question, index }) => {
    const isEditing = editingId === question.question_id;
    const [weight, setWeight] = useState(question.weight);
    const [isRequired, setIsRequired] = useState(question.is_required);

    const handleSaveEdit = () => {
      onUpdate(question.question_id, {
        weight: weight === 'Info' ? 'Info' : parseInt(weight) || 10,
        is_required: isRequired,
      });
      setEditingId(null);
    };

    const handleCancelEdit = () => {
      setWeight(question.weight);
      setIsRequired(question.is_required);
      setEditingId(null);
    };

    return (
      <div
        draggable
        onDragStart={() => handleDragStart(index)}
        onDragOver={(e) => handleDragOver(e, index)}
        onDragEnd={handleDragEnd}
        className={`p-4 rounded-lg border-2 transition-all ${
          draggedIndex === index
            ? 'border-opex-cyan bg-cyan-50 shadow-lg scale-[1.02]'
            : 'border-gray-200 bg-white hover:border-gray-300'
        }`}
      >
        <div className="flex items-start space-x-3">
          {/* Drag Handle */}
          <div className="cursor-move text-gray-400 hover:text-gray-600 pt-1">
            <GripVertical size={20} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Question Number and Text */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-xs font-bold text-opex-navy bg-opex-navy/10 px-2 py-1 rounded">
                    Q{index + 1}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                    {question.category}
                  </span>
                  {question.is_required && (
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                      Required
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-900 font-medium">
                  {question.question_text}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-1 ml-2">
                {!isEditing && (
                  <>
                    <button
                      onClick={() => setEditingId(question.question_id)}
                      className="p-1 hover:bg-gray-100 rounded transition-colors"
                      title="Edit question settings"
                      aria-label="Edit question settings"
                    >
                      <Edit2 size={16} className="text-gray-600" />
                    </button>
                    <button
                      onClick={() => onRemove(question.question_id)}
                      className="p-1 hover:bg-red-50 rounded transition-colors"
                      title="Remove question"
                      aria-label="Remove question"
                    >
                      <X size={16} className="text-red-600" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Edit Mode */}
            {isEditing ? (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Weight
                    </label>
                    <select
                      value={weight}
                      onChange={(e) => setWeight(e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-opex-cyan"
                    >
                      <option value="Info">Info (No Score)</option>
                      <option value="5">5 points</option>
                      <option value="10">10 points</option>
                      <option value="15">15 points</option>
                      <option value="20">20 points</option>
                      <option value="25">25 points</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isRequired}
                        onChange={(e) => setIsRequired(e.target.checked)}
                        className="w-4 h-4 text-opex-navy focus:ring-opex-cyan rounded"
                      />
                      <span className="text-sm text-gray-700">Required</span>
                    </label>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleSaveEdit}
                    className="flex-1 flex items-center justify-center space-x-1 px-3 py-1.5 bg-opex-navy text-white rounded text-sm font-medium hover:bg-opex-navy/90 transition-colors"
                  >
                    <Check size={16} />
                    <span>Save</span>
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="flex-1 px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                <span className="px-2 py-1 bg-gray-100 rounded">
                  {question.input_type}
                </span>
                <span>Weight: {question.weight === 'Info' ? 'Info' : `${question.weight} pts`}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
          <FileText size={24} />
          <span>Selected Questions</span>
        </h2>
        <span className="text-sm text-gray-600">{questions.length} questions</span>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Drag questions to reorder them. Click the edit icon to change weight and required status.
        </p>
      </div>

      {/* Questions List */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {questions.length > 0 ? (
          questions.map((question, index) => (
            <QuestionItem key={question.question_id} question={question} index={index} />
          ))
        ) : (
          <div className="text-center py-12">
            <FileText size={48} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-600 font-medium mb-1">No questions added yet</p>
            <p className="text-sm text-gray-500">
              Browse the question database on the left to add questions
            </p>
          </div>
        )}
      </div>

      {/* Summary */}
      {questions.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Total Questions:</span>
            <span className="font-bold text-gray-900">{questions.length}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">Total Points:</span>
            <span className="font-bold text-gray-900">
              {questions.reduce((sum, q) => {
                const weight = q.weight === 'Info' ? 0 : parseInt(q.weight) || 0;
                return sum + weight;
              }, 0)} points
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">Required Questions:</span>
            <span className="font-bold text-gray-900">
              {questions.filter(q => q.is_required).length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SelectedQuestionsList;
