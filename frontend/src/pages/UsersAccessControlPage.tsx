import React, { useEffect, useMemo, useState } from 'react';
import { Box, Tab, Tabs } from '@mui/material';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext.tsx';
import {
  canManageAccessControl,
  canViewUserRoleAssignment,
  canViewUsersSection,
} from '../utils/permissions.ts';
import { UsersPage } from './UsersPage.tsx';
import { AccessControlPage } from './AccessControlPage.tsx';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';

type SectionTab = 'users' | 'roles' | 'userRoles';

export const UsersAccessControlPage: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const availableTabs = useMemo(() => {
    const tabs: SectionTab[] = [];
    if (canViewUsersSection(user)) tabs.push('users');
    if (canManageAccessControl(user)) tabs.push('roles');
    if (canViewUserRoleAssignment(user)) tabs.push('userRoles');
    return tabs;
  }, [user]);

  const tabFromQuery = searchParams.get('tab') as SectionTab | null;
  const initialTab = tabFromQuery && availableTabs.includes(tabFromQuery)
    ? tabFromQuery
    : availableTabs[0] ?? 'users';

  const [activeTab, setActiveTab] = useState<SectionTab>(initialTab);

  useEffect(() => {
    if (!availableTabs.includes(activeTab)) {
      setActiveTab(availableTabs[0] ?? 'users');
    }
  }, [activeTab, availableTabs]);

  useEffect(() => {
    if (tabFromQuery && availableTabs.includes(tabFromQuery) && tabFromQuery !== activeTab) {
      setActiveTab(tabFromQuery);
    }
  }, [tabFromQuery, availableTabs, activeTab]);

  const handleTabChange = (_: React.SyntheticEvent, index: number) => {
    const next = availableTabs[index];
    if (!next) return;
    setActiveTab(next);
    setSearchParams({ tab: next });
  };

  const tabIndex = Math.max(0, availableTabs.indexOf(activeTab));

  return (
    <Box>
      <RivarPageHeader
        title={t('navigation.usersAccessControl')}
        subtitle={t('accessControl.unifiedSubtitle')}
      />

      <Tabs value={tabIndex} onChange={handleTabChange} sx={{ mb: 2 }}>
        {availableTabs.includes('users') && <Tab label={t('navigation.users')} />}
        {availableTabs.includes('roles') && <Tab label={t('accessControl.rolesTab')} />}
        {availableTabs.includes('userRoles') && <Tab label={t('accessControl.userRolesTab')} />}
      </Tabs>

      {activeTab === 'users' && <UsersPage embedded />}
      {activeTab === 'roles' && <AccessControlPage embedded mode="roles" />}
      {activeTab === 'userRoles' && <AccessControlPage embedded mode="userRoles" />}
    </Box>
  );
};
