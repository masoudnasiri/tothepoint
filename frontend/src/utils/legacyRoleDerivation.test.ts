import { deriveLegacyRoleFromRoleCodes } from './legacyRoleDerivation.ts';

describe('deriveLegacyRoleFromRoleCodes', () => {
  it('maps system_admin to admin', () => {
    expect(deriveLegacyRoleFromRoleCodes(['system_admin'])).toBe('admin');
  });

  it('uses precedence when multiple system roles are selected', () => {
    expect(deriveLegacyRoleFromRoleCodes(['project_manager', 'pmo'])).toBe('pmo');
  });

  it('defaults to pm for custom-only role selection', () => {
    expect(deriveLegacyRoleFromRoleCodes(['qa_custom'])).toBe('pm');
  });

  it('maps procurement_specialist to procurement', () => {
    expect(deriveLegacyRoleFromRoleCodes(['procurement_specialist'])).toBe('procurement');
  });
});
