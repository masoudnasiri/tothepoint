/**
 * Utility functions for error handling
 */

export const formatApiError = (error: any, fallbackMessage: string = 'An error occurred'): string => {
  const errorDetail = error?.response?.data?.detail;
  
  // Handle array of validation errors (Pydantic format)
  if (Array.isArray(errorDetail)) {
    return errorDetail.map(e => e.msg || e.message || String(e)).join(', ');
  }
  
  // Handle string errors
  if (typeof errorDetail === 'string') {
    return errorDetail;
  }
  
  // Handle object errors (extract message if possible)
  if (errorDetail && typeof errorDetail === 'object') {
    if (errorDetail.msg) return errorDetail.msg;
    if (errorDetail.message) return errorDetail.message;
    // If object has no extractable message, stringify it
    return JSON.stringify(errorDetail);
  }
  
  // Fallback to error message
  if (error?.message) {
    return error.message;
  }
  
  return fallbackMessage;
};
