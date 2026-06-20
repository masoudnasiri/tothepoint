import React from 'react';
import { Box, Typography } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarPanelProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  noPadding?: boolean;
  sx?: object;
}

export const RivarPanel: React.FC<RivarPanelProps> = ({
  title,
  subtitle,
  actions,
  children,
  noPadding = false,
  sx = {},
}) => (
  <Box
    sx={{
      background: rivarTokens.paper,
      border: `1px solid ${rivarTokens.line}`,
      borderRadius: rivarTokens.radiusLg,
      boxShadow: rivarTokens.shadowCard,
      overflow: 'hidden',
      ...sx,
    }}
  >
    {(title || actions) && (
      <Box
        display="flex"
        alignItems="flex-start"
        justifyContent="space-between"
        sx={{
          px: 3,
          py: 2,
          borderBottom: `1px solid ${rivarTokens.line}`,
        }}
      >
        <Box>
          {title && (
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 600, color: rivarTokens.ink, lineHeight: 1.4 }}
            >
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="caption" sx={{ color: rivarTokens.ink500, display: 'block', mt: 0.25 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        {actions && (
          <Box display="flex" alignItems="center" gap={1}>
            {actions}
          </Box>
        )}
      </Box>
    )}
    <Box sx={noPadding ? {} : { p: 3 }}>{children}</Box>
  </Box>
);
