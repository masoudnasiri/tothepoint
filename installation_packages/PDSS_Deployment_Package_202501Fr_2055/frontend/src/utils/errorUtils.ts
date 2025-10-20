/**
 * Utility functions for error handling
 */

export const formatApiError = (error: any, fallbackMessage: string = 'An error occurred'): string => {
  const errorDetail = error?.response?.data?.detail;
  
  if (Array.isArray(errorDetail)) {
    return errorDetail.map(e => e.msg || e.message || String(e)).join(', ');
  }
  
  if (typeof errorDetail === 'string') {
    return errorDetail;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  return fallbackMessage;
};
