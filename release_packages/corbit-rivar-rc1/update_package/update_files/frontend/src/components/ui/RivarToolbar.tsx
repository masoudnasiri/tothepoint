import React from 'react';
import { Box } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarToolbarProps {
  left?: React.ReactNode;
  right?: React.ReactNode;
  children?: React.ReactNode;
  sx?: object;
}

export const RivarToolbar: React.FC<RivarToolbarProps> = ({ left, right, children, sx = {} }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 1.5,
      mb: 2,
      flexWrap: 'wrap',
      ...sx,
    }}
  >
    {left && (
      <Box display="flex" alignItems="center" gap={1.25} flexWrap="wrap" sx={{ flex: 1, minWidth: 0 }}>
        {left}
      </Box>
    )}
    {children}
    {right && (
      <Box display="flex" alignItems="center" gap={1} flexShrink={0} flexWrap="wrap">
        {right}
      </Box>
    )}
  </Box>
);
