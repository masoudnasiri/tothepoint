import React from 'react';
import { Box, Typography } from '@mui/material';
import { rivarTokens } from '../../theme/rivarTheme.ts';

interface RivarCoverageRingProps {
  percent: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
}

export const RivarCoverageRing: React.FC<RivarCoverageRingProps> = ({
  percent,
  size = 80,
  strokeWidth = 7,
  label,
  sublabel,
}) => {
  const clamp = Math.min(100, Math.max(0, percent));
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (clamp / 100) * circ;

  const ringColor =
    clamp >= 100 ? rivarTokens.good :
    clamp >= 70  ? rivarTokens.warn :
                   rivarTokens.risk;

  const bgColor = rivarTokens.surface100;

  return (
    <Box sx={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
      <Box sx={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={bgColor}
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={ringColor}
            strokeWidth={strokeWidth}
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
          />
        </svg>
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            sx={{
              fontFamily: 'ui-monospace, "IBM Plex Mono", monospace',
              fontSize: size < 64 ? '0.75rem' : '0.9375rem',
              fontWeight: 700,
              color: ringColor,
              lineHeight: 1,
            }}
          >
            {Math.round(clamp)}%
          </Typography>
        </Box>
      </Box>
      {label && (
        <Typography sx={{ fontSize: '0.75rem', fontWeight: 500, color: rivarTokens.ink, textAlign: 'center' }}>
          {label}
        </Typography>
      )}
      {sublabel && (
        <Typography sx={{ fontSize: '0.6875rem', color: rivarTokens.ink500, textAlign: 'center', mt: -0.5 }}>
          {sublabel}
        </Typography>
      )}
    </Box>
  );
};
