import React, { useEffect } from 'react';
import { IconButton, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import { Language as LanguageIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    handleClose();
    
    // Update document direction for RTL languages
    if (lng === 'fa') {
      document.documentElement.dir = 'rtl';
      document.documentElement.lang = 'fa';
    } else {
      document.documentElement.dir = 'ltr';
      document.documentElement.lang = 'en';
    }
  };

  // Set initial direction based on current language
  useEffect(() => {
    if (i18n.language === 'fa') {
      document.documentElement.dir = 'rtl';
      document.documentElement.lang = 'fa';
    } else {
      document.documentElement.dir = 'ltr';
      document.documentElement.lang = 'en';
    }
  }, [i18n.language]);

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'fa', name: 'فارسی', flag: '🇮🇷' },
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  return (
    <>
      <IconButton
        onClick={handleClick}
        aria-label="change language"
        title={`Current: ${currentLanguage.name}`}
        size="small"
        sx={{ color: 'text.secondary', '&:hover': { bgcolor: 'action.hover' } }}
      >
        <LanguageIcon sx={{ fontSize: 18 }} />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        {languages.map((language) => (
          <MenuItem
            key={language.code}
            onClick={() => changeLanguage(language.code)}
            selected={i18n.language === language.code}
          >
            <ListItemIcon>
              <span style={{ fontSize: '1.5rem' }}>{language.flag}</span>
            </ListItemIcon>
            <ListItemText>{language.name}</ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};
