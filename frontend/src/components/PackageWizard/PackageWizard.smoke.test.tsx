import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { act } from 'react';
import { PackageWizard } from './PackageWizard.tsx';

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: () => '',
  }),
}));

jest.mock('../../services/api.ts', () => ({
  packagesAPI: {
    listByProjectItem: jest.fn().mockResolvedValue({ data: [] }),
    create: jest.fn().mockResolvedValue({ data: { id: 1 } }),
    update: jest.fn().mockResolvedValue({ data: { id: 1 } }),
    get: jest.fn().mockResolvedValue({ data: { subitems: [] } }),
    deleteSubItem: jest.fn().mockResolvedValue({}),
    createSubItem: jest.fn().mockResolvedValue({}),
  },
  suppliersAPI: {
    list: jest.fn().mockResolvedValue({ data: [] }),
    get: jest.fn().mockResolvedValue({ data: { company_name: 'Supplier 1' } }),
  },
  itemsAPI: {},
  procurementAPI: {
    create: jest.fn().mockResolvedValue({ data: { id: 1 } }),
  },
}));

describe('PackageWizard smoke tests', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('renders create dialog and first step content', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="TEST-001"
          itemName="Test Item"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
        />
      );
    });

    expect(document.body.textContent).toContain('Create Package');
    expect(document.body.textContent).toContain('Metadata');
  });
});
