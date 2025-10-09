import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
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

  const getSelectedNames = () => {
    if (selectedProjects.length === 0) return 'All Projects';
    if (selectedProjects.length === projects.length) return 'All Projects';
    return selectedProjects
      .map(id => projects.find(p => p.id === id)?.project_code)
      .filter(Boolean)
      .join(', ');
  };

  return (
    <FormControl fullWidth size="small" sx={{ minWidth: 250 }}>
      <InputLabel>{label}</InputLabel>
      <Select
        multiple={multiple}
        value={selectedProjects}
        onChange={handleChange}
        label={label}
        renderValue={() => getSelectedNames()}
        disabled={loading}
      >
        <MenuItem
          value={0}
          onClick={() => onChange([])}
        >
          <Checkbox checked={selectedProjects.length === 0} />
          <ListItemText primary="All Projects" />
        </MenuItem>
        {projects.map((project) => (
          <MenuItem key={project.id} value={project.id}>
            <Checkbox checked={selectedProjects.indexOf(project.id) > -1} />
            <ListItemText 
              primary={project.project_code}
              secondary={project.project_name}
            />
          </MenuItem>
        ))}
      </Select>
      {selectedProjects.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
          {selectedProjects.map(projectId => {
            const project = projects.find(p => p.id === projectId);
            return project ? (
              <Chip
                key={projectId}
                label={project.project_code}
                size="small"
                onDelete={() => onChange(selectedProjects.filter(id => id !== projectId))}
              />
            ) : null;
          })}
        </Box>
      )}
    </FormControl>
  );
};

