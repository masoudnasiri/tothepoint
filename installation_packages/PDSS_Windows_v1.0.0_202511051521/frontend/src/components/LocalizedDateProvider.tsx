import React from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { useTranslation } from 'react-i18next';
// Adapters
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
// Jalali (Persian) adapter - requires @mui/x-date-pickers >= v6
// If you don't have this package, run: npm i @mui/x-date-pickers
// No extra install needed beyond x-date-pickers
import { AdapterDateFnsJalali } from '@mui/x-date-pickers/AdapterDateFnsJalali';

type Props = { children: React.ReactNode };

export const LocalizedDateProvider: React.FC<Props> = ({ children }) => {
  const { i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const isFa = lang.startsWith('fa');

  if (isFa) {
    return (
      <LocalizationProvider dateAdapter={AdapterDateFnsJalali} adapterLocale={undefined}>
        {children}
      </LocalizationProvider>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      {children}
    </LocalizationProvider>
  );
};

export default LocalizedDateProvider;


