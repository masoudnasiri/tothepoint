import React, { useEffect, useState } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Avatar,
  IconButton,
  Divider,
  Menu,
  MenuItem,
  Collapse,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Business,
  ShoppingCart,
  LocalShipping,
  AccountBalance,
  Analytics,
  People,
  Logout,
  Tune,
  CheckCircle,
  Psychology,
  Inventory,
  Assessment,
  Insights,
  ExpandLess,
  ExpandMore,
  Info,
  AdminPanelSettings,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { canManageAccessControl } from '../utils/permissions.ts';
import { LanguageSwitcher } from './LanguageSwitcher.tsx';
import { useTranslation } from 'react-i18next';
import { BRAND_NAME, PRODUCER_NAME, PRODUCT_NAME, getRuntimeVersion } from '../utils/appIdentity.ts';
import { rivarTokens } from '../theme/rivarTheme.ts';

const DRAWER_WIDTH = rivarTokens.sidebarWidth;

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  textKey: string;
  icon: React.ReactNode;
  path?: string;
  roles: string[];
  children?: NavigationItem[];
  accessControlOnly?: boolean;
}

const navigationItems: NavigationItem[] = [
  { textKey: 'navigation.dashboard', icon: <Dashboard />, path: '/dashboard', roles: ['admin', 'pmo', 'pm', 'procurement', 'finance'] },
  {
    textKey: 'navigation.insights',
    icon: <Insights />,
    roles: ['admin', 'pmo', 'pm', 'procurement', 'finance'],
    children: [
      { textKey: 'navigation.projectAnalytics', icon: <Analytics />, path: '/analytics', roles: ['admin', 'pmo', 'pm', 'finance'] },
      { textKey: 'navigation.reports', icon: <Assessment />, path: '/reports', roles: ['admin', 'pmo', 'procurement', 'finance'] },
    ],
  },
  { textKey: 'navigation.projects', icon: <Business />, path: '/projects', roles: ['admin', 'pmo', 'pm', 'finance'] },
  { textKey: 'navigation.procurement', icon: <ShoppingCart />, path: '/procurement', roles: ['admin', 'procurement', 'finance'] },
  { textKey: 'navigation.procurementPlan', icon: <LocalShipping />, path: '/procurement-plan', roles: ['admin', 'procurement', 'pm', 'pmo', 'finance'] },
  { textKey: 'navigation.finance', icon: <AccountBalance />, path: '/finance', roles: ['admin', 'finance'] },
  { textKey: 'navigation.optimization', icon: <Psychology />, path: '/optimization-enhanced', roles: ['admin', 'finance'] },
  { textKey: 'navigation.decisions', icon: <CheckCircle />, path: '/decisions', roles: ['admin', 'finance'] },
  { textKey: 'navigation.users', icon: <People />, path: '/users', roles: ['admin'] },
  {
    textKey: 'navigation.accessControl',
    icon: <AdminPanelSettings />,
    path: '/access-control',
    roles: ['admin'],
    accessControlOnly: true,
  },
  { textKey: 'navigation.auditLogs', icon: <Info />, path: '/audit-logs', roles: ['admin'] },
  {
    textKey: 'navigation.baseInformation',
    icon: <Info />,
    roles: ['admin', 'pmo', 'pm', 'procurement', 'finance'],
    children: [
      { textKey: 'navigation.weights', icon: <Tune />, path: '/weights', roles: ['admin'] },
      { textKey: 'navigation.itemsMaster', icon: <Inventory />, path: '/items-master', roles: ['admin', 'pmo', 'pm', 'finance'] },
      { textKey: 'navigation.suppliers', icon: <Business />, path: '/suppliers', roles: ['admin', 'pmo', 'pm', 'procurement', 'finance'] },
    ],
  },
];

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(['navigation.insights']));
  const [appVersion, setAppVersion] = useState<string>('...');
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';

  useEffect(() => {
    let mounted = true;
    getRuntimeVersion().then((v) => { if (mounted) setAppVersion(v); });
    return () => { mounted = false; };
  }, []);

  // Auto-expand parent groups that contain the active child
  useEffect(() => {
    const newExpanded = new Set(expandedItems);
    const checkExpand = (items: NavigationItem[]) => {
      for (const item of items) {
        if (item.children) {
          const hasActive = item.children.some(c => c.path && location.pathname === c.path);
          if (hasActive) newExpanded.add(item.textKey);
          checkExpand(item.children);
        }
      }
    };
    checkExpand(navigationItems);
    setExpandedItems(newExpanded);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  const isItemActive = (item: NavigationItem): boolean => {
    if (item.path && location.pathname === item.path) return true;
    if (item.children) return item.children.some(c => isItemActive(c));
    return false;
  };

  const canSeeNavItem = (item: NavigationItem): boolean => {
    if (item.accessControlOnly) {
      return canManageAccessControl(user);
    }
    return Boolean(user?.role && item.roles.includes(user.role));
  };

  const filteredNavItems = navigationItems.filter(canSeeNavItem);

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  const handleSubmenuToggle = (key: string) => {
    const next = new Set(expandedItems);
    next.has(key) ? next.delete(key) : next.add(key);
    setExpandedItems(next);
  };

  const getPageTitle = () => {
    const find = (items: NavigationItem[]): string | null => {
      for (const item of items) {
        if (item.path && location.pathname === item.path) return item.textKey;
        if (item.children) {
          const r = find(item.children);
          if (r) return r;
        }
      }
      return null;
    };
    return t(find(navigationItems) || 'navigation.dashboard');
  };

  const userInitials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : '??';

  const renderNavItem = (item: NavigationItem, level: number = 0) => {
    const isExpanded = expandedItems.has(item.textKey);
    const isActive = isItemActive(item);
    const hasChildren = !!(item.children && item.children.length > 0);
    const filteredChildren = item.children?.filter(canSeeNavItem) || [];

    return (
      <React.Fragment key={item.textKey}>
        <ListItem disablePadding sx={{ mb: 0 }}>
          <ListItemButton
            selected={isActive && !hasChildren}
            onClick={() => {
              if (hasChildren) {
                handleSubmenuToggle(item.textKey);
              } else if (item.path) {
                handleNavigation(item.path);
              }
            }}
            sx={{
              flexDirection: isRTL ? 'row-reverse' : 'row',
              pl: isRTL ? 1.25 : 1.25 + level * 2,
              pr: 1.25,
              borderRadius: '8px',
              minHeight: 36,
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 32,
                mr: isRTL ? 0 : 1,
                ml: isRTL ? 1 : 0,
                justifyContent: 'center',
                '& svg': {
                  fontSize: 16,
                  color: isActive ? rivarTokens.accent600 : rivarTokens.ink300,
                },
              }}
            >
              {item.icon}
            </ListItemIcon>
            <ListItemText
              primary={t(item.textKey)}
              sx={{
                textAlign: isRTL ? 'right' : 'left',
                '& .MuiListItemText-primary': {
                  fontSize: '0.84375rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? rivarTokens.accent600 : rivarTokens.ink700,
                },
              }}
            />
            {hasChildren && (
              <Box sx={{ ml: isRTL ? 0 : 'auto', mr: isRTL ? 'auto' : 0, color: rivarTokens.ink300 }}>
                {isExpanded ? <ExpandLess sx={{ fontSize: 15 }} /> : <ExpandMore sx={{ fontSize: 15 }} />}
              </Box>
            )}
          </ListItemButton>
        </ListItem>

        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List disablePadding sx={{ pl: isRTL ? 0 : 1, pr: isRTL ? 1 : 0 }}>
              {filteredChildren.map(child => renderNavItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  const sidebarContent = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Brand */}
      <Box
        sx={{
          px: 2,
          pt: 2.5,
          pb: 2.5,
          borderBottom: `1px solid ${rivarTokens.line}`,
        }}
      >
        <Box display="flex" alignItems="center" gap={1.25}>
          <Box
            component="img"
            src="/rivar.png"
            alt="Rivar logo"
            sx={{ width: 28, height: 28, objectFit: 'contain', borderRadius: '6px' }}
          />
          <Box>
            <Typography
              sx={{
                fontWeight: 700,
                fontSize: '0.9375rem',
                color: rivarTokens.ink,
                lineHeight: 1.2,
              }}
            >
              {PRODUCT_NAME}
            </Typography>
            <Typography
              sx={{
                fontFamily: 'ui-monospace, monospace',
                fontSize: '0.65rem',
                color: rivarTokens.ink300,
                lineHeight: 1.3,
              }}
            >
              {PRODUCER_NAME}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', px: 1, py: 1.5 }}>
        <List disablePadding>
          {filteredNavItems.map(item => renderNavItem(item))}
        </List>
      </Box>

      {/* Version footer */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          borderTop: `1px solid ${rivarTokens.line}`,
        }}
      >
        <Typography
          sx={{
            fontFamily: 'ui-monospace, monospace',
            fontSize: '0.65rem',
            color: rivarTokens.ink300,
          }}
        >
          {BRAND_NAME} · v{appVersion}
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box
      className={isRTL ? 'persian-theme' : ''}
      sx={{ display: 'flex', direction: isRTL ? 'rtl' : 'ltr', minHeight: '100vh' }}
    >
      {/* ── Sidebar ── */}
      <Box
        component="nav"
        sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          anchor={isRTL ? 'right' : 'left'}
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              direction: isRTL ? 'rtl' : 'ltr',
            },
          }}
        >
          {sidebarContent}
        </Drawer>

        {/* Desktop permanent drawer */}
        <Drawer
          variant="permanent"
          anchor={isRTL ? 'right' : 'left'}
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              direction: isRTL ? 'rtl' : 'ltr',
            },
          }}
          open
        >
          {sidebarContent}
        </Drawer>
      </Box>

      {/* ── Main content ── */}
      <Box
        component="main"
        className={isRTL ? 'persian-theme' : ''}
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          background: rivarTokens.surface,
          direction: isRTL ? 'rtl' : 'ltr',
          overflow: 'hidden',
        }}
      >
        {/* Topbar */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: 56,
            px: { xs: 2, sm: 4 },
            background: rivarTokens.paper,
            borderBottom: `1px solid ${rivarTokens.line}`,
            position: 'sticky',
            top: 0,
            zIndex: 100,
            flexShrink: 0,
            flexDirection: isRTL ? 'row-reverse' : 'row',
          }}
        >
          {/* Mobile: hamburger */}
          <IconButton
            onClick={() => setMobileOpen(true)}
            sx={{ display: { sm: 'none' }, mr: isRTL ? 0 : 1, ml: isRTL ? 1 : 0 }}
          >
            <MenuIcon sx={{ fontSize: 20 }} />
          </IconButton>

          {/* Page title */}
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              fontSize: '1rem',
              color: rivarTokens.ink,
              flex: 1,
              textAlign: isRTL ? 'right' : 'left',
              noWrap: true,
            }}
          >
            {getPageTitle()}
          </Typography>

          {/* Right slot: lang switcher + user */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              flexDirection: isRTL ? 'row-reverse' : 'row',
            }}
          >
            <LanguageSwitcher />

            <Tooltip title={`${user?.username} · ${user?.role}`}>
              <IconButton
                onClick={(e) => setAnchorEl(e.currentTarget)}
                size="small"
                sx={{ p: 0.5 }}
              >
                <Avatar
                  sx={{
                    width: 30,
                    height: 30,
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    background: rivarTokens.ink,
                    color: '#fff',
                  }}
                >
                  {userInitials}
                </Avatar>
              </IconButton>
            </Tooltip>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={() => setAnchorEl(null)}
              anchorOrigin={{ vertical: 'bottom', horizontal: isRTL ? 'left' : 'right' }}
              transformOrigin={{ vertical: 'top', horizontal: isRTL ? 'left' : 'right' }}
              PaperProps={{
                sx: {
                  mt: 0.5,
                  minWidth: 180,
                  border: `1px solid ${rivarTokens.line}`,
                  boxShadow: rivarTokens.shadowPanel,
                },
              }}
            >
              <Box sx={{ px: 2, py: 1.5, borderBottom: `1px solid ${rivarTokens.line}` }}>
                <Typography sx={{ fontWeight: 600, fontSize: '0.875rem', color: rivarTokens.ink }}>
                  {user?.username}
                </Typography>
                <Typography sx={{ fontSize: '0.75rem', color: rivarTokens.ink500, textTransform: 'capitalize' }}>
                  {user?.role}
                </Typography>
              </Box>
              <MenuItem
                onClick={() => {
                  logout();
                  navigate('/login');
                  setAnchorEl(null);
                }}
                sx={{
                  flexDirection: isRTL ? 'row-reverse' : 'row',
                  gap: 1.5,
                  fontSize: '0.8125rem',
                  color: rivarTokens.risk,
                  py: 1.25,
                }}
              >
                <Logout sx={{ fontSize: 16 }} />
                {t('auth.logout')}
              </MenuItem>
            </Menu>
          </Box>
        </Box>

        {/* Page content */}
        <Box
          className={isRTL ? 'persian-theme' : ''}
          sx={{
            flex: 1,
            p: { xs: 2, sm: 3, md: 4 },
            overflowY: 'auto',
            direction: isRTL ? 'rtl' : 'ltr',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};
