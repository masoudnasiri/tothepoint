import { useState, useEffect, useContext, createContext, ReactNode } from 'react';
import api from '../services/api.ts';

export interface FeatureFlags {
  enable_package_procurement: boolean;
  legacy_project_item_fallback: boolean;
  supplier_normalization_enforced: boolean;
  enable_package_based_optimization: boolean;
  require_package_id_for_new_options: boolean;
}

interface FeatureFlagsContextType {
  flags: FeatureFlags | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  isPackageMode: boolean;
  allowLegacyFallback: boolean;
  hasOverrides: boolean;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextType | undefined>(undefined);

// QA override support (non-production only)
const QA_OVERRIDE_STORAGE_KEY = 'qa_feature_flags_override';
const getQAOverride = (): Partial<FeatureFlags> | null => {
  if (process.env.NODE_ENV === 'production') return null;
  try {
    const stored = localStorage.getItem(QA_OVERRIDE_STORAGE_KEY);
    if (stored) {
      const override = JSON.parse(stored);
      return override;
    }
  } catch (e) {
    // Silently fail - QA override is optional
  }
  return null;
};

const setQAOverride = (override: Partial<FeatureFlags> | null): void => {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  if (override) {
    localStorage.setItem(QA_OVERRIDE_STORAGE_KEY, JSON.stringify(override));
  } else {
    localStorage.removeItem(QA_OVERRIDE_STORAGE_KEY);
  }
};

export const useFeatureFlags = () => {
  const context = useContext(FeatureFlagsContext);
  if (!context) {
    throw new Error('useFeatureFlags must be used within FeatureFlagsProvider');
  }
  return context;
};

export const FeatureFlagsProvider = ({ children }: { children: ReactNode }) => {
  const [flags, setFlags] = useState<FeatureFlags | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFlags = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      // Avoid noisy 401/403 calls on public/login pages.
      // Feature flags are forced to package mode below anyway.
      if (!token) {
        setFlags({
          enable_package_procurement: true,
          legacy_project_item_fallback: false,
          supplier_normalization_enforced: false,
          enable_package_based_optimization: false,
          require_package_id_for_new_options: false,
        });
        return;
      }

      const response = await api.get('/config/feature-flags');
      let fetchedFlags = response.data as FeatureFlags;

      // Apply QA override if present (non-production only)
      const qaOverride = getQAOverride();
      if (qaOverride) {
        fetchedFlags = { ...fetchedFlags, ...qaOverride };
      }

      // Package mode is always enabled (legacy removed)
      fetchedFlags = {
        ...fetchedFlags,
        enable_package_procurement: true,
        legacy_project_item_fallback: false,
      };

      setFlags(fetchedFlags);
    } catch (err: any) {
      console.error('Failed to fetch feature flags:', err);
      setError(err?.response?.data?.detail || 'Failed to load feature flags');
      // Package mode is always enabled (legacy removed)
      setFlags({
        enable_package_procurement: true,
        legacy_project_item_fallback: false,
        supplier_normalization_enforced: false,
        enable_package_based_optimization: false,
        require_package_id_for_new_options: false,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlags();
  }, []);

  // Package mode is always enabled (legacy removed)
  const isPackageMode = true;
  const allowLegacyFallback = false;
  const hasOverrides = getQAOverride() !== null;

  return (
    <FeatureFlagsContext.Provider
      value={{
        flags,
        loading,
        error,
        refresh: fetchFlags,
        isPackageMode,
        allowLegacyFallback,
        hasOverrides,
      }}
    >
      {children}
    </FeatureFlagsContext.Provider>
  );
};

// QA override utility (non-production only)
export const setFeatureFlagsOverride = (override: Partial<FeatureFlags> | null): void => {
  setQAOverride(override);
  // Trigger a page reload to apply the override
  if (process.env.NODE_ENV !== 'production') {
    window.location.reload();
  }
};

export const getFeatureFlagsOverride = (): Partial<FeatureFlags> | null => {
  return getQAOverride();
};

