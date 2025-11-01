import React from 'react';
import { Box, Typography, BoxProps } from '@mui/material';

interface ResponsivePageHeaderProps extends BoxProps {
  title: string;
  actions?: React.ReactNode;
}

export const ResponsivePageHeader: React.FC<ResponsivePageHeaderProps> = ({ 
  title, 
  actions,
  ...boxProps 
}) => {
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', sm: 'center' },
        gap: { xs: 1, sm: 2 },
        mb: 3,
        ...boxProps.sx
      }}
      {...boxProps}
    >
      <Typography 
        variant="h4" 
        sx={{ 
          fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' },
          fontWeight: 500
        }}
      >
        {title}
      </Typography>
      {actions && (
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 1, 
            width: { xs: '100%', sm: 'auto' } 
          }}
        >
          {actions}
        </Box>
      )}
    </Box>
  );
};
