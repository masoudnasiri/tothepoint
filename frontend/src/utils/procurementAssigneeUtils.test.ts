import { filterProcurementCapableUsers, formatUserLabel } from './procurementAssigneeUtils.ts';

describe('procurementAssigneeUtils', () => {
  const users = [
    {
      id: 1,
      username: 'proc1',
      role: 'procurement',
      created_at: '',
      is_active: true,
    },
    {
      id: 2,
      username: 'inactive',
      role: 'procurement',
      created_at: '',
      is_active: false,
    },
    {
      id: 3,
      username: 'pm1',
      role: 'pm',
      created_at: '',
      is_active: true,
      roles: [{ code: 'project_manager', display_name: 'Project Manager', is_system: true }],
    },
    {
      id: 4,
      username: 'rbac_proc',
      role: 'pm',
      created_at: '',
      is_active: true,
      roles: [{ code: 'procurement_specialist', display_name: 'Procurement Specialist', is_system: true }],
    },
  ];

  it('filters active procurement-capable users', () => {
    const filtered = filterProcurementCapableUsers(users);
    expect(filtered.map((u) => u.id)).toEqual([1, 4]);
  });

  it('formats user label with role hint', () => {
    expect(formatUserLabel(users[0])).toContain('proc1');
    expect(formatUserLabel(users[3])).toContain('Procurement Specialist');
  });
});
