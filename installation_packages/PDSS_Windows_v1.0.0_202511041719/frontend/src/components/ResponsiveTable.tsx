import React from 'react';
import { TableContainer, Paper, TableContainerProps } from '@mui/material';

export const ResponsiveTable: React.FC<TableContainerProps> = ({ children, ...props }) => {
  return (
    <TableContainer 
      component={Paper}
      sx={{
        width: '100%',
        overflowX: 'auto',
        ...props.sx
      }}
      {...props}
    >
      {children}
    </TableContainer>
  );
};
