import React from 'react';
import { Box, Typography, Divider } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarSectionProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  divider?: boolean;
  sx?: object;
}

export const RivarSection: React.FC<RivarSectionProps> = ({
  title,
  description,
  children,
  divider = false,
  sx = {},
}) => (
  <Box sx={{ mb: 3, ...sx }}>
    {title && (
      <Typography
        variant="body2"
        sx={{
          fontWeight: 600,
          color: rivarTokens.ink,
          fontSize: '0.8125rem',
          mb: description ? 0.5 : 1.5,
        }}
      >
        {title}
      </Typography>
    )}
    {description && (
      <Typography variant="caption" sx={{ color: rivarTokens.ink500, display: 'block', mb: 1.5 }}>
        {description}
      </Typography>
    )}
    {children}
    {divider && <Divider sx={{ mt: 3 }} />}
  </Box>
);
