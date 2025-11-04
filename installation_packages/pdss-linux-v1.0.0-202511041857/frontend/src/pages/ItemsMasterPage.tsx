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
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Preview as PreviewIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { itemsMasterAPI } from '../services/api.ts';
import { ItemMaster, ItemMasterCreate } from '../types/index.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';

export const ItemsMasterPage: React.FC = () => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDateTime = useMemo(() => (dateString: string) => {
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd HH:mm') : gregorianFormat(d, 'yyyy-MM-dd HH:mm');
    } catch {
      return new Date(dateString).toLocaleString();
    }
  }, [isFa]);
  
  const [items, setItems] = useState<ItemMaster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ItemMaster | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [previewedCode, setPreviewedCode] = useState('');
  const [codeExists, setCodeExists] = useState(false);
  
  const [formData, setFormData] = useState<ItemMasterCreate>({
    company: '',
    item_name: '',
    model: '',
    part_number: '',
    category: '',
    unit: 'piece',
    description: '',
  });
  // Sub-items state
  const [subItems, setSubItems] = useState<any[]>([]);
  const [subItemForm, setSubItemForm] = useState<{ name: string; description?: string; part_number?: string }>({ name: '', description: '', part_number: '' });
  const [subItemsLoading, setSubItemsLoading] = useState(false);
  const [draftSubItems, setDraftSubItems] = useState<Array<{ name: string; description?: string; part_number?: string }>>([]);

  const canEdit = user?.role === 'admin' || user?.role === 'pm' || user?.role === 'pmo' || user?.role === 'finance';

  useEffect(() => {
    fetchItems();
  }, []);

  // Auto-preview item code as user types
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.company && formData.item_name) {
        previewItemCode();
      } else {
        setPreviewedCode('');
        setCodeExists(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [formData.company, formData.item_name, formData.model]);

  const fetchItems = async () => {
    try {
      const response = await itemsMasterAPI.list({ active_only: true });
      setItems(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubItems = async (itemId: number) => {
    setSubItemsLoading(true);
    try {
      const res = await itemsMasterAPI.listSubItems(itemId);
      setSubItems(res.data || []);
    } catch (e) {
      // noop
      setSubItems([]);
    } finally {
      setSubItemsLoading(false);
    }
  };

  const previewItemCode = async () => {
    try {
      const response = await itemsMasterAPI.previewCode(
        formData.company,
        formData.item_name,
        formData.model || undefined
      );
      setPreviewedCode(response.data.item_code);
      
      // If we're editing and the code matches the current item, it's not a duplicate
      if (selectedItem && response.data.item_code === selectedItem.item_code) {
        setCodeExists(false);
      } else {
        setCodeExists(response.data.exists);
      }
    } catch (err: any) {
      setPreviewedCode('');
      setCodeExists(false);
    }
  };

  const handleCreateItem = async () => {
    try {
      const res = await itemsMasterAPI.create(formData);
      const created = res.data;
      // If user drafted sub-items during create, persist them now
      if (created?.id && draftSubItems.length > 0) {
        try {
          await Promise.all(draftSubItems.map(d => itemsMasterAPI.createSubItem(created.id, d)));
        } catch (e) {
          console.error('Failed creating some sub-items', e);
        }
      }
      setCreateDialogOpen(false);
      resetForm();
      fetchItems();
      setSuccess(t('itemsMaster.itemCreatedSuccessfully'));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('itemsMaster.failedToCreateItem'));
    }
  };

  const handleEditItem = async () => {
    if (!selectedItem) return;

    try {
      await itemsMasterAPI.update(selectedItem.id, formData);
      setEditDialogOpen(false);
      setSelectedItem(null);
      resetForm();
      fetchItems();
      setSuccess(t('itemsMaster.itemUpdatedSuccessfully'));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('itemsMaster.failedToUpdateItem'));
    }
  };

  const handleDeleteItem = async (itemId: number, itemCode: string) => {
    if (!window.confirm(t('itemsMaster.confirmDeleteItem', { itemCode }))) return;

    try {
      await itemsMasterAPI.delete(itemId);
      fetchItems();
      setSuccess(t('itemsMaster.itemDeletedSuccessfully'));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('itemsMaster.failedToDeleteItem'));
    }
  };

  const resetForm = () => {
    setFormData({
      company: '',
      item_name: '',
      model: '',
      category: '',
      unit: 'piece',
      description: '',
    });
    setPreviewedCode('');
    setCodeExists(false);
    setDraftSubItems([]);
    setSubItemForm({ name: '', description: '', part_number: '' });
  };

  const filteredItems = items.filter(item => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      item.item_code.toLowerCase().includes(search) ||
      item.company.toLowerCase().includes(search) ||
      item.item_name.toLowerCase().includes(search) ||
      (item.model && item.model.toLowerCase().includes(search))
    );
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const renderFormFields = () => (
    <>
      <TextField
        autoFocus
        margin="dense"
        label={t('itemsMaster.companyBrand')}
        fullWidth
        variant="outlined"
        value={formData.company}
        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
        placeholder={t('itemsMaster.companyPlaceholder')}
        sx={{ mb: 2 }}
      />
      <TextField
        margin="dense"
        label={t('itemsMaster.itemName')}
        fullWidth
        variant="outlined"
        value={formData.item_name}
        onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
        placeholder={t('itemsMaster.itemNamePlaceholder')}
        sx={{ mb: 2 }}
      />
      <TextField
        margin="dense"
        label={t('itemsMaster.modelVariant')}
        fullWidth
        variant="outlined"
        value={formData.model}
        onChange={(e) => setFormData({ ...formData, model: e.target.value })}
        placeholder={t('itemsMaster.modelPlaceholder')}
        sx={{ mb: 2 }}
      />

      <TextField
        margin="dense"
        label={t('itemsMaster.partNumber') || 'Part Number'}
        fullWidth
        variant="outlined"
        value={formData.part_number || ''}
        onChange={(e) => setFormData({ ...formData, part_number: e.target.value })}
        placeholder={t('itemsMaster.partNumberPlaceholder') || 'e.g., PN-ABC-1234'}
        sx={{ mb: 2 }}
      />

      {/* Live Preview of Generated Code */}
      {previewedCode && (
        <Paper 
          elevation={0}
          sx={{ 
            p: 2, 
            mb: 2, 
            bgcolor: codeExists ? 'error.lighter' : 'success.lighter',
            border: '2px solid',
            borderColor: codeExists ? 'error.main' : 'success.main'
          }}
        >
          <Box display="flex" alignItems="center" gap={1}>
            {codeExists ? <CancelIcon color="error" /> : <CheckCircleIcon color="success" />}
            <Box flexGrow={1}>
              <Typography variant="subtitle2" color={codeExists ? 'error.dark' : 'success.dark'}>
                {codeExists ? t('itemsMaster.codeAlreadyExists') : t('itemsMaster.generatedItemCode')}
              </Typography>
              <Typography variant="h6" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                {previewedCode}
              </Typography>
            </Box>
          </Box>
          {codeExists && (
            <Typography variant="caption" color="error">
              {t('itemsMaster.codeAlreadyExists')}
            </Typography>
          )}
        </Paper>
      )}

      <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
        <InputLabel>{t('itemsMaster.category')}</InputLabel>
        <Select
          value={formData.category || ''}
          label={t('itemsMaster.category')}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
        >
          <MenuItem value="">
            <em>{t('common.none')}</em>
          </MenuItem>
          <MenuItem value="IT Equipment">{t('itemsMaster.categoryITEquipment')}</MenuItem>
          <MenuItem value="Network & Communication">{t('itemsMaster.categoryNetworkCommunication')}</MenuItem>
          <MenuItem value="Security & Surveillance">{t('itemsMaster.categorySecuritySurveillance')}</MenuItem>
          <MenuItem value="Software & Licenses">{t('itemsMaster.categorySoftwareLicenses')}</MenuItem>
          <MenuItem value="Storage & Backup">{t('itemsMaster.categoryStorageBackup')}</MenuItem>
          <MenuItem value="Power & Cooling">{t('itemsMaster.categoryPowerCooling')}</MenuItem>
          <MenuItem value="Datacenter Infrastructure">{t('itemsMaster.categoryDatacenter')}</MenuItem>
          <MenuItem value="Office Equipment">{t('itemsMaster.categoryOfficeEquipment')}</MenuItem>
          <MenuItem value="Construction">{t('itemsMaster.categoryConstruction')}</MenuItem>
          <MenuItem value="Electrical">{t('itemsMaster.categoryElectrical')}</MenuItem>
          <MenuItem value="Mechanical">{t('itemsMaster.categoryMechanical')}</MenuItem>
          <MenuItem value="Plumbing">{t('itemsMaster.categoryPlumbing')}</MenuItem>
          <MenuItem value="HVAC">{t('itemsMaster.categoryHVAC')}</MenuItem>
          <MenuItem value="Other">{t('itemsMaster.categoryOther')}</MenuItem>
        </Select>
      </FormControl>
      
      <TextField
        margin="dense"
        label={t('itemsMaster.description')}
        fullWidth
        variant="outlined"
        multiline
        rows={3}
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        placeholder={t('itemsMaster.descriptionPlaceholder')}
        sx={{ mb: 2 }}
      />

      <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
        <InputLabel>{t('itemsMaster.unitRequired')}</InputLabel>
        <Select
          value={formData.unit}
          label={t('itemsMaster.unit')}
          onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
        >
          <MenuItem value="piece">{t('itemsMaster.piece')}</MenuItem>
          <MenuItem value="set">{t('itemsMaster.set')}</MenuItem>
          <MenuItem value="license">{t('itemsMaster.license')}</MenuItem>
          <MenuItem value="subscription">{t('itemsMaster.subscription')}</MenuItem>
          <MenuItem value="meter">{t('itemsMaster.meter')}</MenuItem>
          <MenuItem value="kg">{t('itemsMaster.kilogram')}</MenuItem>
          <MenuItem value="liter">{t('itemsMaster.liter')}</MenuItem>
          <MenuItem value="box">{t('itemsMaster.box')}</MenuItem>
          <MenuItem value="ton">{t('itemsMaster.ton')}</MenuItem>
          <MenuItem value="sqm">{t('itemsMaster.squareMeter')}</MenuItem>
        </Select>
      </FormControl>

      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="caption">
          <strong>{t('itemsMaster.itemCode')}:</strong> {t('itemsMaster.autoGeneratedFormat')}
        </Typography>
      </Alert>
    </>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('itemsMaster.title')}</Typography>
        {canEdit && (
          <Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => {
                setLoading(true);
                fetchItems();
              }}
              sx={{ mr: 1 }}
            >
              {t('common.refresh')}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetForm();
                setSelectedItem(null);
                setCreateDialogOpen(true);
              }}
            >
              {t('itemsMaster.createItem')}
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          {t('itemsMaster.itemsMasterDescription')}
        </Typography>
      </Alert>

      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          label={t('itemsMaster.searchItems')}
          placeholder={t('itemsMaster.searchPlaceholder')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
        />
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('itemsMaster.itemCode')}</TableCell>
              <TableCell>{t('itemsMaster.company')}</TableCell>
              <TableCell>{t('itemsMaster.itemName')}</TableCell>
              <TableCell>{t('itemsMaster.model')}</TableCell>
              <TableCell>{t('itemsMaster.category')}</TableCell>
              <TableCell>{t('itemsMaster.unit')}</TableCell>
              <TableCell>{t('itemsMaster.status')}</TableCell>
              <TableCell align="center">{t('itemsMaster.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    {searchTerm ? t('itemsMaster.noItemsFound') : t('itemsMaster.noItemsYet')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium" sx={{ fontFamily: 'monospace' }}>
                      {item.item_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{item.company}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {item.item_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{item.model || '-'}</Typography>
                  </TableCell>
                  <TableCell>
                    {item.category ? (
                      <Chip label={item.category} size="small" variant="outlined" />
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip label={item.unit} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.is_active ? t('itemsMaster.active') : t('itemsMaster.inactive')}
                      color={item.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    {canEdit && (
                      <>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedItem(item);
                            fetchSubItems(item.id);
                            setViewDialogOpen(true);
                          }}
                          title="View Item"
                          color="primary"
                        >
                          <PreviewIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedItem(item);
                            setFormData({
                              company: item.company,
                              item_name: item.item_name,
                              model: item.model || '',
                              part_number: (item as any).part_number || '',
                              category: item.category || '',
                              unit: item.unit,
                              description: item.description || '',
                            });
                            setEditDialogOpen(true);
                            fetchSubItems(item.id);
                          }}
                          title="Edit Item"
                        >
                          <EditIcon />
                        </IconButton>
                        {user?.role === 'admin' && (
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteItem(item.id, item.item_code)}
                            title="Delete Item"
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Item Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => {
          setCreateDialogOpen(false);
          resetForm();
          setSelectedItem(null);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>{t('itemsMaster.createNewMasterItem')}</DialogTitle>
        <DialogContent>
          {renderFormFields()}

        {/* Sub-Items Draft (Create Mode) */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('itemsMaster.subItems')}
          </Typography>
          {/* Existing drafted sub-items list */}
          <Box sx={{ display: 'grid', gap: 1, mb: 1 }}>
            {draftSubItems.length > 0 ? (
              draftSubItems.map((si, idx) => (
                <Paper key={`${si.name}-${idx}`} sx={{ p: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box flexGrow={1}>
                    <Typography variant="body2" fontWeight="medium">{si.name}</Typography>
                    <Typography variant="caption" color="text.secondary">{si.part_number || '-'}</Typography>
                    {si.description && (
                      <Typography variant="caption" display="block">{si.description}</Typography>
                    )}
                  </Box>
                  <IconButton size="small" color="error" onClick={() => {
                    setDraftSubItems(draftSubItems.filter((_, i) => i !== idx));
                  }}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Paper>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">{t('itemsMaster.noSubItems')}</Typography>
            )}
          </Box>

          {/* Add new draft sub-item */}
          <Box sx={{ display: 'grid', gap: 1 }}>
            <Typography variant="subtitle2">{t('itemsMaster.addSubItem')}</Typography>
            <TextField size="small" label={t('common.name')} value={subItemForm.name} onChange={(e) => setSubItemForm({ ...subItemForm, name: e.target.value })} />
            <TextField size="small" label={t('itemsMaster.partNumber')} value={subItemForm.part_number || ''} onChange={(e) => setSubItemForm({ ...subItemForm, part_number: e.target.value })} />
            <TextField size="small" label={t('common.description')} value={subItemForm.description || ''} onChange={(e) => setSubItemForm({ ...subItemForm, description: e.target.value })} />
            <Button
              variant="contained"
              size="small"
              disabled={!subItemForm.name}
              onClick={() => {
                setDraftSubItems([...draftSubItems, { ...subItemForm }]);
                setSubItemForm({ name: '', description: '', part_number: '' });
              }}
            >
              {t('common.add')}
            </Button>
          </Box>
        </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            resetForm();
            setSelectedItem(null);
          }}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleCreateItem} 
            variant="contained"
            disabled={!formData.company || !formData.item_name || codeExists}
          >
            {t('itemsMaster.createItem')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Item Dialog */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => {
          setEditDialogOpen(false);
          resetForm();
          setSelectedItem(null);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>{t('itemsMaster.editMasterItem')}</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="caption">
                <strong>{t('common.note')}:</strong> {t('itemsMaster.noteCodeRegeneration')}
              </Typography>
            </Alert>
          )}
          {renderFormFields()}

          {/* Sub-Items Management (Edit Only) */}
          {selectedItem && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                {t('itemsMaster.subItems')}
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => fetchSubItems(selectedItem.id)}
                  startIcon={<RefreshIcon />}
                >
                  {t('common.refresh')}
                </Button>
              </Box>
              <Box sx={{ display: 'grid', gap: 1 }}>
                {subItemsLoading ? (
                  <CircularProgress size={20} />
                ) : (subItems && subItems.length > 0 ? (
                  subItems.map((si) => (
                    <Paper key={si.id} sx={{ p: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box flexGrow={1}>
                        <Typography variant="body2" fontWeight="medium">{si.name}</Typography>
                        <Typography variant="caption" color="text.secondary">{si.part_number || '-'}</Typography>
                        {si.description && (
                          <Typography variant="caption" display="block">{si.description}</Typography>
                        )}
                      </Box>
                      {canEdit && (
                        <>
                          <IconButton size="small" onClick={async () => {
                            const name = prompt('Name', si.name) || si.name;
                            const part = prompt('Part Number', si.part_number || '') || si.part_number || '';
                            const desc = prompt('Description', si.description || '') || si.description || '';
                            await itemsMasterAPI.updateSubItem(selectedItem.id, si.id, { name, part_number: part, description: desc });
                            fetchSubItems(selectedItem.id);
                          }}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small" color="error" onClick={async () => {
                            if (!window.confirm('Delete this sub-item?')) return;
                            await itemsMasterAPI.deleteSubItem(selectedItem.id, si.id);
                            fetchSubItems(selectedItem.id);
                          }}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </>
                      )}
                    </Paper>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">{t('itemsMaster.noSubItems')}</Typography>
                ))}
              </Box>

              {canEdit && (
                <Box sx={{ mt: 2, display: 'grid', gap: 1 }}>
                  <TextField size="small" label={t('common.name')} value={subItemForm.name} onChange={(e) => setSubItemForm({ ...subItemForm, name: e.target.value })} />
                  <TextField size="small" label={t('itemsMaster.partNumber')} value={subItemForm.part_number || ''} onChange={(e) => setSubItemForm({ ...subItemForm, part_number: e.target.value })} />
                  <TextField size="small" label={t('common.description')} value={subItemForm.description || ''} onChange={(e) => setSubItemForm({ ...subItemForm, description: e.target.value })} />
                  <Button
                    variant="contained"
                    size="small"
                    disabled={!subItemForm.name}
                    onClick={async () => {
                      await itemsMasterAPI.createSubItem(selectedItem.id, subItemForm);
                      setSubItemForm({ name: '', description: '', part_number: '' });
                      fetchSubItems(selectedItem.id);
                    }}
                  >
                    {t('common.add')}
                  </Button>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setEditDialogOpen(false);
            resetForm();
            setSelectedItem(null);
          }}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleEditItem} 
            variant="contained"
            disabled={!formData.company || !formData.item_name}
          >
            {t('itemsMaster.updateItem')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Item Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('itemsMaster.viewMasterItem')}</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ pt: 2 }}>
              <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'primary.lighter', border: '1px solid', borderColor: 'primary.main' }}>
                <Typography variant="subtitle2" color="primary.dark" gutterBottom>
                  {t('itemsMaster.itemCode')}
                </Typography>
                <Typography variant="h6" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {selectedItem.item_code}
                </Typography>
              </Paper>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('itemsMaster.companyBrand')}
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedItem.company}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('itemsMaster.itemName')}
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedItem.item_name}
                </Typography>
              </Box>

              {selectedItem.model && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('itemsMaster.modelVariant')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedItem.model}
                  </Typography>
                </Box>
              )}

              {(selectedItem as any).part_number && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('itemsMaster.partNumber') || 'Part Number'}
                  </Typography>
                  <Typography variant="body1">
                    {(selectedItem as any).part_number}
                  </Typography>
                </Box>
              )}

              {selectedItem.category && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('itemsMaster.category')}
                  </Typography>
                  <Chip label={selectedItem.category} size="small" variant="outlined" />
                </Box>
              )}

              {selectedItem.description && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('itemsMaster.description')}
                  </Typography>
                  <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedItem.description}
                    </Typography>
                  </Paper>
                </Box>
              )}

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('itemsMaster.unit')}
                </Typography>
                <Chip label={selectedItem.unit} size="small" color="primary" />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('common.status')}
                </Typography>
                <Chip
                  label={selectedItem.is_active ? t('itemsMaster.active') : t('itemsMaster.inactive')}
                  color={selectedItem.is_active ? 'success' : 'default'}
                  size="small"
                />
              </Box>

              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary">
                  {t('itemsMaster.created')}: {formatDisplayDateTime(selectedItem.created_at)}
                </Typography>
              </Box>

              {/* Sub-Items (Read-only in View) */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  {t('itemsMaster.subItems')}
                </Typography>
                <Box sx={{ display: 'grid', gap: 1 }}>
                  {subItemsLoading ? (
                    <CircularProgress size={20} />
                  ) : (subItems && subItems.length > 0 ? (
                    subItems.map((si) => (
                      <Paper key={si.id} sx={{ p: 1.5 }}>
                        <Typography variant="body2" fontWeight="medium">{si.name}</Typography>
                        <Typography variant="caption" color="text.secondary">{si.part_number || '-'}</Typography>
                        {si.description && (
                          <Typography variant="caption" display="block">{si.description}</Typography>
                        )}
                      </Paper>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">{t('itemsMaster.noSubItems')}</Typography>
                  ))}
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {canEdit && (
            <Button
              onClick={() => {
                setViewDialogOpen(false);
                if (selectedItem) {
                  setFormData({
                    company: selectedItem.company,
                    item_name: selectedItem.item_name,
                    model: selectedItem.model || '',
                    category: selectedItem.category || '',
                    unit: selectedItem.unit,
                    description: selectedItem.description || '',
                  });
                  setEditDialogOpen(true);
                }
              }}
              variant="contained"
              startIcon={<EditIcon />}
            >
              {t('common.edit')}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

