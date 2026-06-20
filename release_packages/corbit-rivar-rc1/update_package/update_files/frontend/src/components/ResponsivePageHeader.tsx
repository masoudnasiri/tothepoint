import React from 'react';
import { BoxProps } from '@mui/material';
import { RivarPageHeader } from './ui/RivarPageHeader.tsx';

interface ResponsivePageHeaderProps extends BoxProps {
  title: string;
  actions?: React.ReactNode;
}

/**
 * ResponsivePageHeader — delegates to RivarPageHeader.
 * Preserved for backward compatibility with existing page components.
 */
export const ResponsivePageHeader: React.FC<ResponsivePageHeaderProps> = ({
  title,
  actions,
}) => <RivarPageHeader title={title} actions={actions} />;
