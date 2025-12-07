/**
 * Form Preview Component
 * Shows a preview of the form in a modal
 */

import { useState, useEffect } from 'react';
import { X, ExternalLink, Loader } from 'lucide-react';
import { formBuilderAPI, getErrorMessage } from '../services/formBuilderApi';
import toast from 'react-hot-toast';

const FormPreview = ({ templateId, templateName, questions, onClose }) => {
  const [previewHtml, setPreviewHtml] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (templateId) {
      fetchPreview();
    } else {
      // For new templates, show a basic preview
      generateBasicPreview();
    }
  }, [templateId, questions]);

  // Add Escape key handler
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const fetchPreview = async () => {
    setIsLoading(true);
    try {
      const response = await formBuilderAPI.previewForm({ template_id: templateId });
      if (response.data.success) {
        setPreviewHtml(response.data.data.html);
      }
    } catch (error) {
      console.error('Failed to fetch preview:', error);
      toast.error(getErrorMessage(error));
      generateBasicPreview();
    } finally {
      setIsLoading(false);
    }
  };

  const generateBasicPreview = () => {
    // Generate a simple preview for templates not yet saved
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${templateName || 'Form Preview'}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9fafb;
          }
          .form-container {
            background: white;
            border-radius: 8px;
            padding: 32px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          }
          h1 {
            color: #1a2859;
            margin-bottom: 24px;
          }
          .question {
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e5e7eb;
          }
          .question:last-child {
            border-bottom: none;
          }
          label {
            display: block;
            font-weight: 500;
            margin-bottom: 8px;
            color: #374151;
          }
          .required {
            color: #ef4444;
          }
          input, textarea, select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
          }
          .category {
            display: inline-block;
            background: #e5e7eb;
            color: #6b7280;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 8px;
          }
          .weight {
            color: #6b7280;
            font-size: 12px;
            margin-left: 8px;
          }
        </style>
      </head>
      <body>
        <div class="form-container">
          <h1>${templateName || 'Form Preview'}</h1>
          <p style="color: #6b7280; margin-bottom: 32px;">This is a preview of your form. Save the template to generate the full version.</p>
          ${questions.map((q, index) => `
            <div class="question">
              <span class="category">${q.category}</span>
              <label>
                ${index + 1}. ${q.question_text}
                ${q.is_required ? '<span class="required">*</span>' : ''}
                <span class="weight">(${q.weight === 'Info' ? 'Info' : q.weight + ' pts'})</span>
              </label>
              ${q.input_type === 'textarea' ? '<textarea rows="4"></textarea>' :
                q.input_type === 'select' ? '<select><option>Select...</option></select>' :
                q.input_type === 'number' ? '<input type="number" />' :
                '<input type="text" />'}
            </div>
          `).join('')}
          ${questions.length === 0 ? '<p style="text-align: center; color: #9ca3af;">Add questions to see preview</p>' : ''}
        </div>
      </body>
      </html>
    `;
    setPreviewHtml(html);
  };

  const handleOpenInNewTab = () => {
    const blob = new Blob([previewHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-6xl h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Form Preview</h2>
            <p className="text-sm text-gray-600 mt-1">{templateName}</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleOpenInNewTab}
              className="btn-secondary flex items-center space-x-2"
              title="Open in new tab"
            >
              <ExternalLink size={20} />
              <span className="hidden sm:inline">Open in Tab</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close preview"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Preview Content - Takes remaining space */}
        <div className="flex-1 overflow-hidden min-h-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader className="animate-spin h-12 w-12 text-opex-navy mx-auto mb-4" />
                <p className="text-gray-600">Generating preview...</p>
              </div>
            </div>
          ) : (
            <iframe
              srcDoc={previewHtml}
              className="w-full h-full border-0"
              title="Form Preview"
              sandbox="allow-same-origin"
            />
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200 bg-gray-50 text-center text-sm text-gray-600 flex-shrink-0">
          <p>This is a preview. Save and deploy your template to create the live form.</p>
        </div>
      </div>
    </div>
  );
};

export default FormPreview;
