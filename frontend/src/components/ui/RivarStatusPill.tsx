import React from 'react';
import { Box } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

export type RivarStatusPillVariant = 'good' | 'warn' | 'risk' | 'accent' | 'neutral';

interface RivarStatusPillProps {
  label: string;
  variant?: RivarStatusPillVariant;
  dot?: boolean;
  size?: 'sm' | 'md';
}

const variants: Record<RivarStatusPillVariant, { bg: string; color: string; border: string }> = {
  good:    { bg: rivarTokens.goodTint,    color: rivarTokens.good,       border: rivarTokens.goodLine },
  warn:    { bg: rivarTokens.warnTint,    color: rivarTokens.warn,       border: rivarTokens.warnLine },
  risk:    { bg: rivarTokens.riskTint,    color: rivarTokens.risk,       border: rivarTokens.riskLine },
  accent:  { bg: rivarTokens.accentTint,  color: rivarTokens.accent600,  border: rivarTokens.accentTintStrong },
  neutral: { bg: rivarTokens.surface100,  color: rivarTokens.ink500,     border: rivarTokens.line },
};

export const RivarStatusPill: React.FC<RivarStatusPillProps> = ({
  label,
  variant = 'neutral',
  dot = false,
  size = 'sm',
}) => {
  const v = variants[variant];
  const isMd = size === 'md';

  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontSize: isMd ? '0.8125rem' : '0.75rem',
        fontWeight: 500,
        px: isMd ? '10px' : '8px',
        py: isMd ? '4px' : '2px',
        borderRadius: '20px',
        background: v.bg,
        color: v.color,
        border: `1px solid ${v.border}`,
        whiteSpace: 'nowrap',
        lineHeight: 1.5,
      }}
    >
      {dot && (
        <Box
          component="span"
          sx={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: v.color,
            flexShrink: 0,
          }}
        />
      )}
      {label}
    </Box>
  );
};
