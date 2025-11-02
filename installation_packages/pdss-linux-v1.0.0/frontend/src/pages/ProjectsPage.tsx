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
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CalendarMonth as CalendarIcon,
  FolderOpen as FolderIcon,
  Inventory as InventoryIcon,
  LocalShipping as ShippingIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { projectsAPI, usersAPI } from '../services/api.ts';
import { Project, ProjectSummary, User } from '../types/index.ts';
import { ProjectPhases } from '../components/ProjectPhases.tsx';
import { useTranslation } from 'react-i18next';

export const ProjectsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
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
  const [projectAssignments, setProjectAssignments] = useState<Record<number, number[]>>({});
  const [formData, setFormData] = useState({
    project_code: '',
    name: '',
    priority_weight: 5,
  });

  useEffect(() => {
    fetchProjects();
    fetchPMUsers();
  }, []);

  useEffect(() => {
    // Fetch assignments for all projects after projects are loaded
    if (projects.length > 0) {
      fetchAllProjectAssignments();
    }
  }, [projects]);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('projects.failedToLoadProjects'));
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
      console.error(t('projects.failedToLoadPMUsers'), err);
      // Fallback: Try to get current user's info at least
      setPmUsers([]);
    }
  };

  const fetchAllProjectAssignments = async () => {
    try {
      const assignmentsMap: Record<number, number[]> = {};
      
      // Fetch assignments for all projects in parallel
      const assignmentPromises = projects.map(async (project) => 
        projectsAPI.getAssignments(project.id)
          .then(response => {
            const assignedUserIds = response.data.map((a: any) => a.user_id);
            assignmentsMap[project.id] = assignedUserIds;
          })
          .catch(() => {
            // If fetch fails, set empty array
            assignmentsMap[project.id] = [];
          })
      );
      
      await Promise.all(assignmentPromises);
      setProjectAssignments(assignmentsMap);
    } catch (err) {
      console.error('Failed to fetch project assignments:', err);
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
      await fetchProjects();
      // Refresh assignments after project creation
      await fetchAllProjectAssignments();
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
      console.error(t('projects.failedToLoadAssignments'), err);
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
      await fetchProjects();
      // Refresh assignments after project update
      await fetchAllProjectAssignments();
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
    // Format as IRR (Iranian Rial) with no decimal places
    return new Intl.NumberFormat('en-US', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value) + ' ﷼';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Calculate totals for stat cards
  const totalProjects = projects.length;
  const totalItems = projects.reduce((sum, p) => sum + (p.item_count || 0), 0);
  const totalQuantity = projects.reduce((sum, p) => sum + (p.total_quantity || 0), 0);
  const totalEstimatedCost = projects.reduce((sum, p) => sum + (Number(p.estimated_cost) || 0), 0);
  const totalEstimatedRevenue = projects.reduce((sum, p) => sum + (Number(p.estimated_revenue) || 0), 0);
  // Assume all projects in the list are active (API filters for user)
  const activeProjects = totalProjects;

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('projects.title')}</Typography>
        {(user?.role === 'admin' || user?.role === 'pmo') && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setFormData({
                project_code: '',
                name: '',
                priority_weight: 5,
              });
              setSelectedProject(null);
              setSelectedPMs([]);
              setCreateDialogOpen(true);
            }}
          >
            {t('projects.createProject')}
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Stat Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="subtitle2">
                    Total Projects
                  </Typography>
                  <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                    {formatNumber(totalProjects)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {activeProjects} active
                  </Typography>
                </Box>
                <Box sx={{ 
                  bgcolor: 'rgba(25, 118, 210, 0.1)', 
                  borderRadius: '50%', 
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <FolderIcon sx={{ fontSize: 40, color: '#1976d2' }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="subtitle2">
                    Total Items
                  </Typography>
                  <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold', color: '#2e7d32' }}>
                    {formatNumber(totalItems)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Across all projects
                  </Typography>
                </Box>
                <Box sx={{ 
                  bgcolor: 'rgba(46, 125, 50, 0.1)', 
                  borderRadius: '50%', 
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <InventoryIcon sx={{ fontSize: 40, color: '#2e7d32' }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="subtitle2">
                    Total Quantity
                  </Typography>
                  <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold', color: '#ed6c02' }}>
                    {formatNumber(totalQuantity)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Units to procure
                  </Typography>
                </Box>
                <Box sx={{ 
                  bgcolor: 'rgba(237, 108, 2, 0.1)', 
                  borderRadius: '50%', 
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <ShippingIcon sx={{ fontSize: 40, color: '#ed6c02' }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="subtitle2">
                    Total Invoice Value
                  </Typography>
                  <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold', color: '#9c27b0' }}>
                    {formatCurrency(totalEstimatedRevenue || 0)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Expected revenue
                  </Typography>
                </Box>
                <Box sx={{ 
                  bgcolor: 'rgba(156, 39, 176, 0.1)', 
                  borderRadius: '50%', 
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <MoneyIcon sx={{ fontSize: 40, color: '#9c27b0' }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('projects.projectCode')}</TableCell>
              <TableCell>{t('projects.projectName')}</TableCell>
              <TableCell align="left">{t('projects.projectManager')}</TableCell>
              <TableCell align="right">{t('projects.items')}</TableCell>
              <TableCell align="right">{t('projects.totalQuantity')}</TableCell>
              <TableCell align="right">{t('projects.totalInvoiceValue')}</TableCell>
              {(user?.role === 'admin' || user?.role === 'finance') && (
                <TableCell align="right">{t('projects.estimatedCost')}</TableCell>
              )}
              <TableCell align="center">{t('projects.actions')}</TableCell>
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
                <TableCell align="left">
                  {projectAssignments[project.id] && projectAssignments[project.id].length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, justifyContent: 'flex-start' }}>
                      {projectAssignments[project.id].map((pmId) => {
                        const pm = pmUsers.find(u => u.id === pmId);
                        return pm ? (
                          <Chip 
                            key={pmId} 
                            label={pm.username} 
                            size="small" 
                            color="primary"
                            variant="outlined"
                          />
                        ) : null;
                      })}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {t('projects.noProjectManager')}
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="right">
                  <Chip label={project.item_count} size="small" />
                </TableCell>
                <TableCell align="right">{project.total_quantity}</TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight="medium" color="primary">
                    {formatCurrency(Number(project.estimated_revenue) || 0)}
                  </Typography>
                </TableCell>
                {(user?.role === 'admin' || user?.role === 'finance') && (
                  <TableCell align="right">
                    <Typography variant="body2" color="text.secondary">
                      {formatCurrency(Number(project.estimated_cost) || 0)}
                    </Typography>
                  </TableCell>
                )}
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => handleViewItems(project.id)}
                    title={t('projects.viewItems')}
                  >
                    <ViewIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleViewPhases(project.id, project.name)}
                    title={t('projects.viewPhases')}
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
                        title={t('projects.editProject')}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteProject(project.id)}
                        title={t('projects.deleteProject')}
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
            label={t('projects.projectCode')}
            fullWidth
            variant="outlined"
            value={formData.project_code}
            onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('projects.projectName')}
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('projects.priority')}
            type="number"
            fullWidth
            variant="outlined"
            value={formData.priority_weight}
            onChange={(e) => setFormData({ ...formData, priority_weight: parseInt(e.target.value) || 5 })}
            inputProps={{ min: 1, max: 10 }}
            helperText={t('projects.priorityWeightHelper')}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Assign Project Managers</InputLabel>
            <Select
              multiple
              value={selectedPMs}
              onChange={(e) => setSelectedPMs(typeof e.target.value === 'string' ? [] : e.target.value)}
              input={<OutlinedInput label={t('projects.assignProjectManagers')} />}
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
            label={t('projects.projectCode')}
            fullWidth
            variant="outlined"
            value={formData.project_code}
            onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('projects.projectName')}
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('projects.priority')}
            type="number"
            fullWidth
            variant="outlined"
            value={formData.priority_weight}
            onChange={(e) => setFormData({ ...formData, priority_weight: parseInt(e.target.value) || 5 })}
            inputProps={{ min: 1, max: 10 }}
            helperText={t('projects.priorityWeightHelper')}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Assigned Project Managers</InputLabel>
            <Select
              multiple
              value={selectedPMs}
              onChange={(e) => setSelectedPMs(typeof e.target.value === 'string' ? [] : e.target.value)}
              input={<OutlinedInput label={t('projects.assignedProjectManagers')} />}
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
              {t('projects.addRemoveProjectManagers')}
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
