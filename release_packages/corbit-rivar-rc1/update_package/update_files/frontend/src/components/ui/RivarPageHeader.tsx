import React from 'react';
import { Box, Typography } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarPageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const RivarPageHeader: React.FC<RivarPageHeaderProps> = ({ title, subtitle, actions }) => (
  <Box
    display="flex"
    alignItems="flex-start"
    justifyContent="space-between"
    mb={3}
    gap={2}
    sx={{ flexWrap: { xs: 'wrap', sm: 'nowrap' } }}
  >
    <Box>
      <Typography
        variant="h5"
        component="h1"
        sx={{
          fontWeight: 600,
          color: rivarTokens.ink,
          letterSpacing: '-0.01em',
          lineHeight: 1.3,
        }}
      >
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="body2" sx={{ mt: 0.5, color: rivarTokens.ink500 }}>
          {subtitle}
        </Typography>
      )}
    </Box>
    {actions && (
      <Box display="flex" alignItems="center" gap={1} flexShrink={0} sx={{ flexWrap: 'wrap' }}>
        {actions}
      </Box>
    )}
  </Box>
);
