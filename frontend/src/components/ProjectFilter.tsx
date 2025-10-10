import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  SelectChangeEvent,
} from '@mui/material';
import { projectsAPI } from '../services/api.ts';

interface Project {
  id: number;
  project_code: string;
  project_name: string;
}

interface ProjectFilterProps {
  selectedProjects: number[];
  onChange: (projectIds: number[]) => void;
  label?: string;
  multiple?: boolean;
}

export const ProjectFilter: React.FC<ProjectFilterProps> = ({
  selectedProjects,
  onChange,
  label = 'Filter by Project(s)',
  multiple = true,
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (err) {
      console.error('Failed to load projects for filter:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (event: SelectChangeEvent<number[]>) => {
    const value = event.target.value;
    onChange(typeof value === 'string' ? [] : value as number[]);
  };

  return (
    <FormControl fullWidth sx={{ minWidth: 250 }}>
      <InputLabel>{label}</InputLabel>
      <Select
        multiple={multiple}
        value={selectedProjects}
        onChange={handleChange}
        label={label}
        disabled={loading}
        renderValue={(selected) => {
          if (selected.length === 0) {
            return <Box sx={{ color: 'text.secondary' }}>All Projects</Box>;
          }
          return (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((id) => {
                const project = projects.find(p => p.id === id);
                return project ? (
                  <Chip key={id} label={project.project_code} size="small" />
                ) : null;
              })}
            </Box>
          );
        }}
      >
        {projects.map((project) => (
          <MenuItem key={project.id} value={project.id}>
            {project.project_code} - {project.project_name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

