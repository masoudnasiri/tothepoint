import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarEmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const RivarEmptyState: React.FC<RivarEmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      py: 7,
      px: 3,
      textAlign: 'center',
    }}
  >
    {icon && (
      <Box sx={{ mb: 2, opacity: 0.35, fontSize: 48, color: rivarTokens.ink300, '& svg': { fontSize: 'inherit' } }}>
        {icon}
      </Box>
    )}
    <Typography
      variant="subtitle1"
      sx={{ fontWeight: 600, color: rivarTokens.ink700, mb: 0.75 }}
    >
      {title}
    </Typography>
    {description && (
      <Typography variant="body2" sx={{ color: rivarTokens.ink300, maxWidth: 360, mb: actionLabel ? 2.5 : 0 }}>
        {description}
      </Typography>
    )}
    {actionLabel && onAction && (
      <Button variant="contained" size="small" onClick={onAction}>
        {actionLabel}
      </Button>
    )}
  </Box>
);
