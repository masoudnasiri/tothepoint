/**
 * Utility functions for error handling
 */

export const formatApiError = (error: any, fallbackMessage: string = 'An error occurred', context?: 'save' | 'load' | 'delete'): string => {
  // Handle network errors (no response from server)
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      if (context === 'save') {
        return 'Request timed out while saving. Please check your connection and try again.';
      }
      return 'Request timed out. Please check your connection and try again.';
    }
    if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
      if (context === 'save') {
        return 'Network error while saving. Please check your connection and try again.';
      }
      if (context === 'load') {
        return 'Network error while loading. Please check your connection and refresh the page.';
      }
      return 'Network error. Please check your connection.';
    }
    if (error.message) {
      return error.message;
    }
    return 'Network error. Please check your connection.';
  }
  
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
