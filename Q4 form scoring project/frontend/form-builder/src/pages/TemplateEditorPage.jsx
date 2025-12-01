/**
 * Template Editor Page
 * Complete template creation and editing interface
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, Eye, Upload, ArrowLeft, Loader, Copy } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';
import QuestionBrowser from '../components/QuestionBrowser';
import SelectedQuestionsList from '../components/SelectedQuestionsList';
import FormPreview from '../components/FormPreview';
import ConfirmDialog from '../components/ConfirmDialog';

const TemplateEditorPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;

  // Template metadata
  const [templateName, setTemplateName] = useState('');
  const [opportunityType, setOpportunityType] = useState('');
  const [opportunitySubtype, setOpportunitySubtype] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('draft');

  // Questions
  const [selectedQuestions, setSelectedQuestions] = useState([]);

  // UI State
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null, variant: 'danger' });

  // Load template if editing
  useEffect(() => {
    if (isEditing) {
      loadTemplate();
    }
  }, [id]);

  const loadTemplate = async () => {
    setIsLoading(true);
    try {
      const response = await formBuilderAPI.getTemplate(id);
      if (response.data.success) {
        const template = response.data.data;
        setTemplateName(template.template_name);
        setOpportunityType(template.opportunity_type);
        setOpportunitySubtype(template.opportunity_subtype);
        setDescription(template.description || '');
        setStatus(template.status);
        setSelectedQuestions(template.questions || []);
      }
    } catch (error) {
      console.error('Failed to load template:', error);
      toast.error(getErrorMessage(error));
      navigate('/templates');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddQuestion = (question) => {
    // Check if already added
    if (selectedQuestions.find(q => q.question_id === question.question_id)) {
      toast.error('Question already added');
      return;
    }

    const newQuestion = {
      question_id: question.question_id,
      question_text: question.question_text,
      category: question.category,
      input_type: question.input_type,
      weight: question.default_weight || 10,
      is_required: true,
      sort_order: selectedQuestions.length + 1,
    };

    setSelectedQuestions([...selectedQuestions, newQuestion]);
    toast.success('Question added');
  };

  const handleRemoveQuestion = (questionId) => {
    const updated = selectedQuestions.filter(q => q.question_id !== questionId);
    // Reorder
    const reordered = updated.map((q, index) => ({
      ...q,
      sort_order: index + 1,
    }));
    setSelectedQuestions(reordered);
  };

  const handleUpdateQuestion = (questionId, updates) => {
    const updated = selectedQuestions.map(q =>
      q.question_id === questionId ? { ...q, ...updates } : q
    );
    setSelectedQuestions(updated);
  };

  const handleReorderQuestions = (reorderedQuestions) => {
    const withOrder = reorderedQuestions.map((q, index) => ({
      ...q,
      sort_order: index + 1,
    }));
    setSelectedQuestions(withOrder);
  };

  const validateTemplate = () => {
    if (!templateName.trim()) {
      toast.error('Template name is required');
      return false;
    }
    if (!opportunityType) {
      toast.error('Opportunity type is required');
      return false;
    }
    if (!opportunitySubtype) {
      toast.error('Opportunity subtype is required');
      return false;
    }
    if (selectedQuestions.length === 0) {
      toast.error('At least one question is required');
      return false;
    }
    return true;
  };

  const handleSave = async () => {
    if (!validateTemplate()) return;

    setIsSaving(true);
    try {
      const templateData = {
        template_name: templateName,
        opportunity_type: opportunityType,
        opportunity_subtype: opportunitySubtype,
        description: description || null,
        questions: selectedQuestions.map(q => ({
          question_id: q.question_id,
          weight: q.weight === 'Info' ? null : q.weight,
          is_required: q.is_required,
          sort_order: q.sort_order,
        })),
      };

      let response;
      if (isEditing) {
        response = await formBuilderAPI.updateTemplate(id, templateData);
        toast.success('Template updated successfully');
      } else {
        response = await formBuilderAPI.createTemplate(templateData);
        toast.success('Template created successfully');

        // Navigate to edit page for the new template
        const newId = response.data.data.template_id;
        navigate(`/templates/${newId}/edit`, { replace: true });
      }
    } catch (error) {
      console.error('Failed to save template:', error);
      toast.error(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeploy = async () => {
    if (!validateTemplate()) return;

    // Save first if there are unsaved changes
    await handleSave();

    setIsDeploying(true);
    try {
      const response = await formBuilderAPI.deployTemplate(id, {
        commit_message: `Deploy ${templateName}`,
      });

      if (response.data.success) {
        const deployedUrl = response.data.data.deployed_url;
        toast.success('Template deployed successfully!');

        // Show deployed URL
        setTimeout(() => {
          setConfirmDialog({
            isOpen: true,
            title: 'Form Deployed Successfully!',
            message: `Your form has been deployed and is now live.\n\nURL: ${deployedUrl}\n\nWould you like to open it in a new tab?`,
            variant: 'info',
            onConfirm: () => {
              window.open(deployedUrl, '_blank');
              setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null, variant: 'danger' });
            }
          });
        }, 500);
      }
    } catch (error) {
      console.error('Failed to deploy template:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
      });
      toast.error(`Failed to deploy template: ${getErrorMessage(error)}`);
    } finally {
      setIsDeploying(false);
    }
  };

  const handleDuplicate = async () => {
    setIsDuplicating(true);
    try {
      const response = await formBuilderAPI.duplicateTemplate(id);

      if (response.data.success) {
        const newTemplate = response.data.data;
        toast.success('Template duplicated successfully!');
        // Navigate to the new template
        navigate(`/templates/${newTemplate.template_id}/edit`);
      }
    } catch (error) {
      console.error('Failed to duplicate template:', error);
      toast.error(`Failed to duplicate template: ${getErrorMessage(error)}`);
    } finally {
      setIsDuplicating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader className="animate-spin h-12 w-12 text-opex-navy mx-auto mb-4" />
          <p className="text-gray-600">Loading template...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/templates')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {isEditing ? 'Edit Template' : 'Create New Template'}
            </h1>
            <p className="text-gray-600 mt-1">
              {isEditing ? `Editing: ${templateName}` : 'Build your form by selecting questions'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="btn-secondary flex items-center space-x-2"
          >
            <Eye size={20} />
            <span>{showPreview ? 'Hide' : 'Preview'}</span>
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary flex items-center space-x-2"
          >
            {isSaving ? (
              <>
                <Loader className="animate-spin" size={20} />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save size={20} />
                <span>Save</span>
              </>
            )}
          </button>
          {isEditing && (
            <>
              <button
                onClick={handleDuplicate}
                disabled={isDuplicating}
                className="btn-secondary flex items-center space-x-2"
              >
                {isDuplicating ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    <span>Duplicating...</span>
                  </>
                ) : (
                  <>
                    <Copy size={20} />
                    <span>Duplicate</span>
                  </>
                )}
              </button>
              <button
                onClick={handleDeploy}
                disabled={isDeploying}
                className="btn-success flex items-center space-x-2"
              >
                {isDeploying ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    <span>Deploying...</span>
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    <span>Deploy</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Template Metadata Form */}
      <div className="card mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Template Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Template Name *</label>
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="input-field"
              placeholder="e.g., SASE Security Assessment"
              required
            />
          </div>

          <div>
            <label className="label">Opportunity Type *</label>
            <select
              value={opportunityType}
              onChange={(e) => setOpportunityType(e.target.value)}
              className="input-field"
              required
            >
              <option value="">Select type...</option>
              <option value="Security">Security</option>
              <option value="Network">Network</option>
              <option value="Cloud">Cloud</option>
              <option value="Managed Service Provider">Managed Service Provider</option>
              <option value="Contact Center">Contact Center</option>
              <option value="Data Center">Data Center</option>
              <option value="Expense Management">Expense Management</option>
            </select>
          </div>

          <div>
            <label className="label">Opportunity Subtype *</label>
            <input
              type="text"
              value={opportunitySubtype}
              onChange={(e) => setOpportunitySubtype(e.target.value)}
              className="input-field"
              placeholder="e.g., SASE, SD-WAN, MDR"
              required
            />
          </div>

          <div>
            <label className="label">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input-field"
              disabled
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="label">Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field"
              rows="3"
              placeholder="Brief description of this form template..."
            />
          </div>
        </div>
      </div>

      {/* Editor Layout: Question Browser + Selected Questions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Question Browser */}
        <div>
          <QuestionBrowser
            onAddQuestion={handleAddQuestion}
            selectedQuestionIds={selectedQuestions.map(q => q.question_id)}
            opportunitySubtype={opportunitySubtype}
          />
        </div>

        {/* Right: Selected Questions */}
        <div>
          <SelectedQuestionsList
            questions={selectedQuestions}
            onRemove={handleRemoveQuestion}
            onUpdate={handleUpdateQuestion}
            onReorder={handleReorderQuestions}
          />
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <FormPreview
          templateId={id}
          templateName={templateName}
          questions={selectedQuestions}
          onClose={() => setShowPreview(false)}
        />
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null, variant: 'danger' })}
        confirmText="Open in New Tab"
        cancelText="Close"
        variant={confirmDialog.variant}
      />
    </div>
  );
};

export default TemplateEditorPage;
