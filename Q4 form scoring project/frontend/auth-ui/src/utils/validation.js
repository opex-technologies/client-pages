/**
 * Form Validation Utilities
 * Matches backend validation rules
 * Created: November 5, 2025
 */

import config from '../config';

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateEmail = (email) => {
  if (!email) {
    return 'Email is required';
  }

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  if (!emailRegex.test(email)) {
    return 'Invalid email format';
  }

  if (email.length > 255) {
    return 'Email too long (max 255 characters)';
  }

  return null;
};

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {string|null} Error message or null if valid
 */
export const validatePassword = (password) => {
  if (!password) {
    return 'Password is required';
  }

  if (password.length < config.password.minLength) {
    return `Password must be at least ${config.password.minLength} characters`;
  }

  if (password.length > 128) {
    return 'Password too long (max 128 characters)';
  }

  if (config.password.requireUppercase && !/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter';
  }

  if (config.password.requireLowercase && !/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter';
  }

  if (config.password.requireDigit && !/\d/.test(password)) {
    return 'Password must contain at least one digit';
  }

  if (config.password.requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return 'Password must contain at least one special character';
  }

  return null;
};

/**
 * Validate full name
 * @param {string} fullName - Full name to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateFullName = (fullName) => {
  if (!fullName) {
    return 'Full name is required';
  }

  if (fullName.trim().length < 2) {
    return 'Full name must be at least 2 characters';
  }

  if (fullName.length > 100) {
    return 'Full name too long (max 100 characters)';
  }

  return null;
};

/**
 * Validate password confirmation
 * @param {string} password - Original password
 * @param {string} confirmPassword - Confirmation password
 * @returns {string|null} Error message or null if valid
 */
export const validatePasswordConfirm = (password, confirmPassword) => {
  if (!confirmPassword) {
    return 'Please confirm your password';
  }

  if (password !== confirmPassword) {
    return 'Passwords do not match';
  }

  return null;
};

/**
 * Get password strength indicator
 * @param {string} password - Password to check
 * @returns {Object} {strength: string, score: number, color: string}
 */
export const getPasswordStrength = (password) => {
  if (!password) {
    return { strength: 'None', score: 0, color: 'gray' };
  }

  let score = 0;

  // Length
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;

  // Character variety
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

  // Determine strength
  if (score <= 2) {
    return { strength: 'Weak', score, color: 'red' };
  } else if (score <= 4) {
    return { strength: 'Fair', score, color: 'yellow' };
  } else if (score <= 6) {
    return { strength: 'Good', score, color: 'blue' };
  } else {
    return { strength: 'Strong', score, color: 'green' };
  }
};
