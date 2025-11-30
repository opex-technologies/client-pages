/**
 * ConfirmDialog Component
 * Reusable confirmation dialog with accessibility features
 */

import { useEffect, useRef } from 'react';
import { X, AlertTriangle, Info } from 'lucide-react';

const ConfirmDialog = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger' // 'danger' or 'info'
}) => {
  const confirmButtonRef = useRef(null);
  const cancelButtonRef = useRef(null);

  // Focus management and keyboard handling
  useEffect(() => {
    if (!isOpen) return;

    // Focus the appropriate button based on variant
    const buttonToFocus = variant === 'danger' ? cancelButtonRef : confirmButtonRef;
    buttonToFocus.current?.focus();

    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    const handleTab = (e) => {
      if (e.key === 'Tab') {
        const confirmBtn = confirmButtonRef.current;
        const cancelBtn = cancelButtonRef.current;

        if (e.shiftKey) {
          if (document.activeElement === cancelBtn) {
            e.preventDefault();
            confirmBtn?.focus();
          }
        } else {
          if (document.activeElement === confirmBtn) {
            e.preventDefault();
            cancelBtn?.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleEscape);
    document.addEventListener('keydown', handleTab);

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleTab);
    };
  }, [isOpen, onCancel, variant]);

  if (!isOpen) return null;

  const variantStyles = {
    danger: {
      icon: AlertTriangle,
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      confirmButton: 'bg-red-600 hover:bg-red-700 text-white',
    },
    info: {
      icon: Info,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      confirmButton: 'bg-opex-cyan hover:bg-opex-cyan/90 text-white',
    }
  };

  const styles = variantStyles[variant];
  const Icon = styles.icon;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
        <div className="p-6">
          {/* Header with Icon */}
          <div className="flex items-start mb-4">
            <div className={`flex-shrink-0 ${styles.iconBg} rounded-full p-3 mr-4`}>
              <Icon className={styles.iconColor} size={24} />
            </div>
            <div className="flex-1">
              <h2
                id="dialog-title"
                className="text-xl font-bold text-gray-900 mb-2"
              >
                {title}
              </h2>
              <p
                id="dialog-description"
                className="text-gray-600 text-sm whitespace-pre-line"
              >
                {message}
              </p>
            </div>
            <button
              onClick={onCancel}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 ml-2"
              aria-label="Close dialog"
            >
              <X size={20} />
            </button>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              ref={cancelButtonRef}
              onClick={onCancel}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium rounded-lg transition-colors duration-200"
            >
              {cancelText}
            </button>
            <button
              ref={confirmButtonRef}
              onClick={onConfirm}
              className={`px-4 py-2 font-medium rounded-lg transition-colors duration-200 ${styles.confirmButton}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
