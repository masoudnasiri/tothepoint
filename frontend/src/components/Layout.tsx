import React, { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Avatar,
  Menu,
  MenuItem,
  Divider,
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
  AccountCircle,
  Logout,
  Tune,
  CheckCircle,
  Psychology,
  Inventory,
  Assessment,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import { LanguageSwitcher } from './LanguageSwitcher.tsx';
import { useTranslation } from 'react-i18next';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  textKey: string;
  icon: React.ReactNode;
  path: string;
  roles: string[];
}

const navigationItems: NavigationItem[] = [
  { textKey: 'navigation.dashboard', icon: <Dashboard />, path: '/dashboard', roles: ['admin', 'pmo', 'pm', 'procurement', 'finance'] },
  { textKey: 'navigation.analytics', icon: <Analytics />, path: '/analytics', roles: ['admin', 'pmo', 'pm', 'finance'] },
  { textKey: 'navigation.reports', icon: <Assessment />, path: '/reports', roles: ['admin', 'pmo', 'procurement', 'finance'] },
  { textKey: 'navigation.projects', icon: <Business />, path: '/projects', roles: ['admin', 'pmo', 'pm', 'finance'] },
  { textKey: 'navigation.procurement', icon: <ShoppingCart />, path: '/procurement', roles: ['admin', 'procurement', 'finance'] },
  { textKey: 'navigation.procurementPlan', icon: <LocalShipping />, path: '/procurement-plan', roles: ['admin', 'procurement', 'pm', 'pmo', 'finance'] },
  { textKey: 'navigation.finance', icon: <AccountBalance />, path: '/finance', roles: ['admin', 'finance'] },
  { textKey: 'navigation.optimization', icon: <Psychology />, path: '/optimization-enhanced', roles: ['admin', 'finance'] },
  { textKey: 'navigation.decisions', icon: <CheckCircle />, path: '/decisions', roles: ['admin', 'finance'] },
  { textKey: 'navigation.users', icon: <People />, path: '/users', roles: ['admin'] },
  { textKey: 'navigation.weights', icon: <Tune />, path: '/weights', roles: ['admin'] },
  { textKey: 'navigation.itemsMaster', icon: <Inventory />, path: '/items-master', roles: ['admin', 'pmo', 'pm', 'finance'] },
];

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  
  // Check if current language is RTL
  const isRTL = i18n.language === 'fa';

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleProfileMenuClose();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  const filteredNavigationItems = navigationItems.filter(item =>
    user?.role && item.roles.includes(user.role)
  );

  const drawer = (
    <div>
      <Toolbar sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
        <Box
          component="img"
          src="/InoTech_b-F.png"
          alt="InoTech Logo"
          sx={{
            width: 140,
            height: 'auto',
            mb: 1,
          }}
        />
        <Typography variant="h6" noWrap component="div" sx={{ textAlign: 'center' }}>
          {t('navigation.procurementDSS')}
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {filteredNavigationItems.map((item) => (
          <ListItem key={item.textKey} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                flexDirection: isRTL ? 'row-reverse' : 'row',
                textAlign: isRTL ? 'right' : 'left',
              }}
            >
              <ListItemIcon sx={{ 
                minWidth: isRTL ? 'auto' : 56,
                mr: isRTL ? 0 : 2,
                ml: isRTL ? 2 : 0,
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={t(item.textKey)} 
                sx={{ 
                  textAlign: isRTL ? 'right' : 'left',
                  '& .MuiListItemText-primary': {
                    textAlign: isRTL ? 'right' : 'left',
                  }
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box 
      className={isRTL ? 'persian-theme' : ''}
      sx={{ display: 'flex', direction: isRTL ? 'rtl' : 'ltr' }}
    >
      <CssBaseline />
      
      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ 
          width: { sm: drawerWidth }, 
          flexShrink: { sm: 0 },
        }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          className={isRTL ? 'persian-theme' : ''}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              direction: isRTL ? 'rtl' : 'ltr',
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          anchor={isRTL ? 'right' : 'left'}
          className={isRTL ? 'persian-theme' : ''}
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              direction: isRTL ? 'rtl' : 'ltr',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content Area */}
      <Box
        component="main"
        className={isRTL ? 'persian-theme' : ''}
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          direction: isRTL ? 'rtl' : 'ltr',
        }}
      >
        <AppBar
          position="fixed"
          sx={{
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            ml: { sm: isRTL ? 0 : `${drawerWidth}px` },
            mr: { sm: isRTL ? `${drawerWidth}px` : 0 },
          }}
        >
          <Toolbar sx={{ direction: isRTL ? 'rtl' : 'ltr' }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ 
                mr: isRTL ? 0 : 2, 
                ml: isRTL ? 2 : 0,
                display: { sm: 'none' } 
              }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, textAlign: isRTL ? 'right' : 'left' }}>
              {t(navigationItems.find(item => item.path === location.pathname)?.textKey || 'navigation.dashboard')}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexDirection: isRTL ? 'row-reverse' : 'row' }}>
              <Typography variant="body2" sx={{ 
                mr: isRTL ? 0 : 2, 
                ml: isRTL ? 2 : 0,
                display: { xs: 'none', sm: 'block' } 
              }}>
                {user?.username} ({user?.role})
              </Typography>
              <LanguageSwitcher />
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="profile-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32 }}>
                  <AccountCircle />
                </Avatar>
              </IconButton>
              <Menu
                id="profile-menu"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: isRTL ? 'left' : 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: isRTL ? 'left' : 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleProfileMenuClose}
              >
                <MenuItem onClick={handleLogout} sx={{ flexDirection: isRTL ? 'row-reverse' : 'row' }}>
                  <ListItemIcon sx={{ 
                    minWidth: isRTL ? 'auto' : 56,
                    mr: isRTL ? 0 : 2,
                    ml: isRTL ? 2 : 0,
                  }}>
                    <Logout fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={t('auth.logout')} />
                </MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>
        
        <Box 
          className={isRTL ? 'persian-theme' : ''}
          sx={{ p: { xs: 1, sm: 2, md: 3 }, overflow: 'auto' }}
        >
          <Toolbar />
          {children}
        </Box>
      </Box>
    </Box>
  );
};
