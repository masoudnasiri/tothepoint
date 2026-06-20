import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Autocomplete,
  Paper,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { suppliersAPI } from '../../services/api.ts';

interface PackageWizardStep1Props {
  data: {
    package_name: string;
    supplier_id: number | null;
    package_type: 'FULL' | 'PARTIAL' | 'CUSTOM';
    description?: string;
  };
  onChange: (updates: Partial<PackageWizardStep1Props['data']>) => void;
}

interface Supplier {
  id: number;
  supplier_id: string;
  company_name: string;
}

export const PackageWizardStep1: React.FC<PackageWizardStep1Props> = ({ data, onChange }) => {
  const { t } = useTranslation();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loadingSuppliers, setLoadingSuppliers] = useState(false);

  useEffect(() => {
    const fetchSuppliers = async () => {
      setLoadingSuppliers(true);
      try {
        const response = await suppliersAPI.list();
        // Handle paginated response structure: response.data.suppliers or direct array
        let suppliersData: Supplier[] = [];
        if (Array.isArray(response.data)) {
          suppliersData = response.data;
        } else if (response.data && Array.isArray(response.data.suppliers)) {
          suppliersData = response.data.suppliers;
        } else if (response.data && Array.isArray(response.data.items)) {
          suppliersData = response.data.items;
        }
        setSuppliers(suppliersData);
      } catch (err) {
        console.error('Failed to load suppliers', err);
        setSuppliers([]); // Ensure suppliers is always an array
      } finally {
        setLoadingSuppliers(false);
      }
    };
    fetchSuppliers();
  }, []);

  // Ensure suppliers is always an array before using .find()
  const selectedSupplier = Array.isArray(suppliers) ? (suppliers.find((s) => s.id === data.supplier_id) || null) : null;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      <Box>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.25 }}>
          {t('procurement.packageMetadata') || 'Package Metadata'}
        </Typography>
        <Typography variant="body2" sx={{ color: '#5B6472' }}>
          {t('procurement.packageMetadataDesc') || 'Define the package identity, type, and supplier.'}
        </Typography>
      </Box>

      <TextField
        fullWidth
        label={t('procurement.packageName') || 'Package Name'}
        value={data.package_name}
        onChange={(e) => onChange({ package_name: e.target.value })}
        required
        helperText={t('procurement.packageNameHelper') || 'Enter a descriptive name for this package'}
      />

      <FormControl fullWidth required>
        <InputLabel>{t('procurement.packageType') || 'Package Type'}</InputLabel>
        <Select
          value={data.package_type}
          label={t('procurement.packageType') || 'Package Type'}
          onChange={(e) => onChange({ package_type: e.target.value as 'FULL' | 'PARTIAL' | 'CUSTOM' })}
        >
          <MenuItem value="FULL">
            {t('procurement.packageTypeFull') || 'Full Package'} - {t('procurement.packageTypeFullDesc') || 'Covers entire project item and all subitems'}
          </MenuItem>
          <MenuItem value="PARTIAL">
            {t('procurement.packageTypePartial') || 'Partial Package'} - {t('procurement.packageTypePartialDesc') || 'Covers subset of subitems'}
          </MenuItem>
          <MenuItem value="CUSTOM">
            {t('procurement.packageTypeCustom') || 'Custom Package'} - {t('procurement.packageTypeCustomDesc') || 'Custom quantity composition'}
          </MenuItem>
        </Select>
      </FormControl>

      <Autocomplete
        fullWidth
        options={Array.isArray(suppliers) ? suppliers : []}
        getOptionLabel={(option) => `${option.company_name} (${option.supplier_id})`}
        value={selectedSupplier}
        onChange={(_, newValue) => onChange({ supplier_id: newValue?.id || null })}
        loading={loadingSuppliers}
        renderInput={(params) => (
          <TextField
            {...params}
            label={t('procurement.supplier') || 'Supplier'}
            required
            helperText={t('procurement.supplierHelper') || 'Select the supplier for this package'}
          />
        )}
        renderOption={(props, option) => (
          <Box component="li" {...props} key={option.id}>
            <Box>
              <Typography variant="body2" fontWeight="medium">
                {option.company_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ID: {option.supplier_id}
              </Typography>
            </Box>
          </Box>
        )}
      />

      <TextField
        fullWidth
        multiline
        rows={3}
        label={t('procurement.description') || 'Description (Optional)'}
        value={data.description || ''}
        onChange={(e) => onChange({ description: e.target.value })}
        helperText={t('procurement.descriptionHelper') || 'Optional notes about this package'}
      />
    </Box>
  );
};

