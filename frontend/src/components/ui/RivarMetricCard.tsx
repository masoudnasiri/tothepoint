import React from 'react';
import { Box, Typography } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

type RivarMetricCardVariant = 'default' | 'good' | 'warn' | 'risk' | 'accent';

interface RivarMetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  subTrend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  variant?: RivarMetricCardVariant;
  sx?: object;
}

const variantColors: Record<RivarMetricCardVariant, { iconBg: string; iconColor: string; valueColor: string }> = {
  default: { iconBg: rivarTokens.surface100, iconColor: rivarTokens.ink500, valueColor: rivarTokens.ink },
  good:    { iconBg: rivarTokens.goodTint,   iconColor: rivarTokens.good,   valueColor: rivarTokens.good },
  warn:    { iconBg: rivarTokens.warnTint,   iconColor: rivarTokens.warn,   valueColor: rivarTokens.warn },
  risk:    { iconBg: rivarTokens.riskTint,   iconColor: rivarTokens.risk,   valueColor: rivarTokens.risk },
  accent:  { iconBg: rivarTokens.accentTint, iconColor: rivarTokens.accent600, valueColor: rivarTokens.accent600 },
};

const trendColors: Record<string, string> = {
  up: rivarTokens.good,
  down: rivarTokens.risk,
  neutral: rivarTokens.ink300,
};

export const RivarMetricCard: React.FC<RivarMetricCardProps> = ({
  label,
  value,
  sub,
  subTrend = 'neutral',
  icon,
  variant = 'default',
  sx = {},
}) => {
  const colors = variantColors[variant];

  return (
    <Box
      sx={{
        background: rivarTokens.paper,
        border: `1px solid ${rivarTokens.line}`,
        borderRadius: rivarTokens.radiusLg,
        boxShadow: rivarTokens.shadowCard,
        p: '18px 20px',
        ...sx,
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.25}>
        <Typography
          sx={{ fontSize: '0.78125rem', fontWeight: 500, color: rivarTokens.ink500 }}
        >
          {label}
        </Typography>
        {icon && (
          <Box
            sx={{
              width: 30,
              height: 30,
              borderRadius: '8px',
              background: colors.iconBg,
              color: colors.iconColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              '& svg': { fontSize: 16 },
            }}
          >
            {icon}
          </Box>
        )}
      </Box>
      <Typography
        sx={{
          fontFamily: 'ui-monospace, "IBM Plex Mono", "Cascadia Code", monospace',
          fontSize: '1.5rem',
          fontWeight: 600,
          letterSpacing: '-0.01em',
          color: colors.valueColor,
          lineHeight: 1.2,
          mb: 0.5,
        }}
      >
        {value}
      </Typography>
      {sub && (
        <Typography
          sx={{
            fontSize: '0.75rem',
            color: trendColors[subTrend] || rivarTokens.ink300,
          }}
        >
          {sub}
        </Typography>
      )}
    </Box>
  );
};
