import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { projectsAPI, usersAPI } from '../services/api.ts';
import { Project, ProjectSummary, User } from '../types/index.ts';
import { ProjectPhases } from '../components/ProjectPhases.tsx';

export const ProjectsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [phasesDialogOpen, setPhasesDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedProjectForPhases, setSelectedProjectForPhases] = useState<number | null>(null);
  const [pmUsers, setPmUsers] = useState<User[]>([]);
  const [selectedPMs, setSelectedPMs] = useState<number[]>([]);
  const [currentAssignments, setCurrentAssignments] = useState<number[]>([]);
  const [formData, setFormData] = useState({
    project_code: '',
    name: '',
    priority_weight: 5,
  });

  useEffect(() => {
    fetchProjects();
    fetchPMUsers();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const fetchPMUsers = async () => {
    try {
      // Use dedicated endpoint that PMO can access
      const response = await usersAPI.listPMs();
      setPmUsers(response.data);
    } catch (err: any) {
      console.error('Failed to load PM users:', err);
      // Fallback: Try to get current user's info at least
      setPmUsers([]);
    }
  };

  const handleCreateProject = async () => {
    try {
      const response = await projectsAPI.create(formData);
      const newProjectId = response.data.id;
      
      // Assign selected PMs to the new project
      if (selectedPMs.length > 0) {
        for (const pmUserId of selectedPMs) {
          try {
            await projectsAPI.assignUser({
              user_id: pmUserId,
              project_id: newProjectId
            });
          } catch (assignErr) {
            console.error(`Failed to assign PM ${pmUserId}:`, assignErr);
          }
        }
      }
      
      setCreateDialogOpen(false);
      setFormData({ project_code: '', name: '', priority_weight: 5 });
      setSelectedPMs([]);
      fetchProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
    }
  };

  const fetchProjectAssignments = async (projectId: number) => {
    try {
      const response = await projectsAPI.getAssignments(projectId);
      const assignedUserIds = response.data.map((a: any) => a.user_id);
      setCurrentAssignments(assignedUserIds);
      setSelectedPMs(assignedUserIds);
    } catch (err: any) {
      console.error('Failed to load assignments:', err);
      setCurrentAssignments([]);
      setSelectedPMs([]);
    }
  };

  const handleEditProject = async () => {
    if (!selectedProject) return;
    
    try {
      // Update project details
      await projectsAPI.update(selectedProject.id, formData);
      
      // ✅ Update PM assignments
      const projectId = selectedProject.id;
      
      // Find PMs to add (in selectedPMs but not in currentAssignments)
      const pmsToAdd = selectedPMs.filter(pmId => !currentAssignments.includes(pmId));
      
      // Find PMs to remove (in currentAssignments but not in selectedPMs)
      const pmsToRemove = currentAssignments.filter(pmId => !selectedPMs.includes(pmId));
      
      // Add new assignments
      for (const pmUserId of pmsToAdd) {
        try {
          await projectsAPI.assignUser({
            user_id: pmUserId,
            project_id: projectId
          });
        } catch (assignErr) {
          console.error(`Failed to assign PM ${pmUserId}:`, assignErr);
        }
      }
      
      // Remove unselected assignments
      for (const pmUserId of pmsToRemove) {
        try {
          await projectsAPI.removeUser(pmUserId, projectId);
        } catch (removeErr) {
          console.error(`Failed to remove PM ${pmUserId}:`, removeErr);
        }
      }
      
      setEditDialogOpen(false);
      setSelectedProject(null);
      setFormData({ project_code: '', name: '', priority_weight: 5 });
      setSelectedPMs([]);
      setCurrentAssignments([]);
      fetchProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update project');
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await projectsAPI.delete(projectId);
      fetchProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project');
    }
  };

  const handleViewItems = (projectId: number) => {
    navigate(`/projects/${projectId}/items`);
  };

  const handleViewPhases = (projectId: number, projectName: string) => {
    setSelectedProjectForPhases(projectId);
    setPhasesDialogOpen(true);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Projects</Typography>
        {(user?.role === 'admin' || user?.role === 'pmo') && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Project
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Project Code</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Items</TableCell>
              <TableCell align="right">Total Quantity</TableCell>
              <TableCell align="right">Estimated Cost</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((project) => (
              <TableRow key={project.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {project.project_code}
                  </Typography>
                </TableCell>
                <TableCell>{project.name}</TableCell>
                <TableCell align="right">
                  <Chip label={project.item_count} size="small" />
                </TableCell>
                <TableCell align="right">{project.total_quantity}</TableCell>
                <TableCell align="right">
                  {formatCurrency(project.estimated_cost)}
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => handleViewItems(project.id)}
                    title="View Items"
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleViewPhases(project.id, project.name)}
                    title="View Phases"
                    color="primary"
                  >
                    <CalendarIcon />
                  </IconButton>
                  {(user?.role === 'admin' || user?.role === 'pmo') && (
                    <>
                      <IconButton
                        size="small"
                        onClick={async () => {
                          // Fetch full project details to get priority_weight
                          const response = await projectsAPI.get(project.id);
                          const fullProject = response.data;
                          setSelectedProject(fullProject);
                          setFormData({
                            project_code: fullProject.project_code,
                            name: fullProject.name,
                            priority_weight: fullProject.priority_weight,
                          });
                          // Fetch current PM assignments
                          await fetchProjectAssignments(fullProject.id);
                          setEditDialogOpen(true);
                        }}
                        title="Edit Project"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteProject(project.id)}
                        title="Delete Project"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Project Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Code"
            fullWidth
            variant="outlined"
            value={formData.project_code}
            onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Priority Weight"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.priority_weight}
            onChange={(e) => setFormData({ ...formData, priority_weight: parseInt(e.target.value) || 5 })}
            inputProps={{ min: 1, max: 10 }}
            helperText="Priority weight for multi-project optimization (1-10)"
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Assign Project Managers</InputLabel>
            <Select
              multiple
              value={selectedPMs}
              onChange={(e) => setSelectedPMs(typeof e.target.value === 'string' ? [] : e.target.value)}
              input={<OutlinedInput label="Assign Project Managers" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((pmId) => {
                    const pm = pmUsers.find(u => u.id === pmId);
                    return pm ? (
                      <Chip key={pmId} label={pm.username} size="small" />
                    ) : null;
                  })}
                </Box>
              )}
            >
              {pmUsers.length === 0 ? (
                <MenuItem disabled>No PM users available</MenuItem>
              ) : (
                pmUsers.map((pm) => (
                  <MenuItem key={pm.id} value={pm.id}>
                    <Checkbox checked={selectedPMs.indexOf(pm.id) > -1} />
                    <ListItemText 
                      primary={pm.username}
                      secondary={pm.role === 'pmo' ? 'PMO' : 'PM'}
                    />
                  </MenuItem>
                ))
              )}
            </Select>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Select one or more Project Managers. They will be able to see and manage this project.
            </Typography>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setSelectedPMs([]);
          }}>
            Cancel
          </Button>
          <Button onClick={handleCreateProject} variant="contained">
            Create & Assign
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Project Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Code"
            fullWidth
            variant="outlined"
            value={formData.project_code}
            onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Priority Weight"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.priority_weight}
            onChange={(e) => setFormData({ ...formData, priority_weight: parseInt(e.target.value) || 5 })}
            inputProps={{ min: 1, max: 10 }}
            helperText="Priority weight for multi-project optimization (1-10)"
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Assigned Project Managers</InputLabel>
            <Select
              multiple
              value={selectedPMs}
              onChange={(e) => setSelectedPMs(typeof e.target.value === 'string' ? [] : e.target.value)}
              input={<OutlinedInput label="Assigned Project Managers" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((pmId) => {
                    const pm = pmUsers.find(u => u.id === pmId);
                    return pm ? (
                      <Chip key={pmId} label={pm.username} size="small" />
                    ) : null;
                  })}
                </Box>
              )}
            >
              {pmUsers.length === 0 ? (
                <MenuItem disabled>No PM users available</MenuItem>
              ) : (
                pmUsers.map((pm) => (
                  <MenuItem key={pm.id} value={pm.id}>
                    <Checkbox checked={selectedPMs.indexOf(pm.id) > -1} />
                    <ListItemText 
                      primary={pm.username}
                      secondary={pm.role === 'pmo' ? 'PMO' : 'PM'}
                    />
                  </MenuItem>
                ))
              )}
            </Select>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Add or remove Project Managers. Changes are applied when you click "Update & Save Assignments".
            </Typography>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setEditDialogOpen(false);
            setSelectedProject(null);
            setSelectedPMs([]);
            setCurrentAssignments([]);
          }}>
            Cancel
          </Button>
          <Button onClick={handleEditProject} variant="contained">
            Update & Save Assignments
          </Button>
        </DialogActions>
      </Dialog>

      {/* Phases Management Dialog */}
      <Dialog 
        open={phasesDialogOpen} 
        onClose={() => setPhasesDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>Manage Project Phases</DialogTitle>
        <DialogContent>
          {selectedProjectForPhases && (
            <ProjectPhases projectId={selectedProjectForPhases} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPhasesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
