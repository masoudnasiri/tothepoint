/**
 * Coverage calculation utilities for package-based procurement
 */

export interface SubItemRequirement {
  sub_item_id: number;
  item_subitem_id?: number; // The actual database ID from project_item_subitems table
  name?: string;
  part_number?: string;
  required_quantity: number;
}

export interface PackageCoverage {
  package_id: number;
  package_name: string;
  package_type: 'FULL' | 'PARTIAL' | 'CUSTOM';
  main_item_quantity: number;
  subitem_coverages: Array<{
    sub_item_id: number;
    covered_quantity: number;
    required_quantity: number;
  }>;
}

export interface CoverageSummary {
  main_item: {
    required: number;
    covered: number;
    remaining: number;
    coverage_percentage: number;
  };
  subitems: Array<{
    sub_item_id: number;
    name?: string;
    part_number?: string;
    required: number;
    covered: number;
    remaining: number;
    coverage_percentage: number;
  }>;
  overall_coverage_percentage: number;
  is_fully_covered: boolean;
}

/**
 * Calculate coverage summary for a project item based on existing packages
 */
export function calculateCoverageSummary(
  mainItemRequiredQuantity: number,
  subItemRequirements: SubItemRequirement[],
  packageCoverages: PackageCoverage[]
): CoverageSummary {
  // Calculate main item coverage
  const mainItemCovered = packageCoverages.reduce(
    (sum, pkg) => sum + pkg.main_item_quantity,
    0
  );
  const mainItemRemaining = Math.max(0, mainItemRequiredQuantity - mainItemCovered);
  const mainItemCoveragePct = mainItemRequiredQuantity > 0
    ? Math.min(100, (mainItemCovered / mainItemRequiredQuantity) * 100)
    : 100;

  // Calculate subitem coverage
  const subitemCoverages = subItemRequirements.map((req) => {
    const covered = packageCoverages.reduce((sum, pkg) => {
      const subitemCoverage = pkg.subitem_coverages.find(
        (sc) => sc.sub_item_id === req.sub_item_id
      );
      return sum + (subitemCoverage?.covered_quantity || 0);
    }, 0);
    const remaining = Math.max(0, req.required_quantity - covered);
    const coveragePct = req.required_quantity > 0
      ? Math.min(100, (covered / req.required_quantity) * 100)
      : 100;

    return {
      sub_item_id: req.sub_item_id,
      name: req.name,
      part_number: req.part_number,
      required: req.required_quantity,
      covered,
      remaining,
      coverage_percentage: coveragePct,
    };
  });

  // Calculate overall coverage (weighted average)
  const totalRequired = mainItemRequiredQuantity + subItemRequirements.reduce(
    (sum, req) => sum + req.required_quantity,
    0
  );
  const totalCovered = mainItemCovered + subitemCoverages.reduce(
    (sum, si) => sum + si.covered,
    0
  );
  const overallCoveragePct = totalRequired > 0
    ? Math.min(100, (totalCovered / totalRequired) * 100)
    : 100;

  const isFullyCovered = mainItemRemaining === 0 && subitemCoverages.every(
    (si) => si.remaining === 0
  );

  return {
    main_item: {
      required: mainItemRequiredQuantity,
      covered: mainItemCovered,
      remaining: mainItemRemaining,
      coverage_percentage: mainItemCoveragePct,
    },
    subitems: subitemCoverages,
    overall_coverage_percentage: overallCoveragePct,
    is_fully_covered: isFullyCovered,
  };
}

/**
 * Calculate remaining demand after applying packages
 */
export function calculateRemainingDemand(
  mainItemRequiredQuantity: number,
  subItemRequirements: SubItemRequirement[],
  packageCoverages: PackageCoverage[]
): {
  main_item_remaining: number;
  subitem_remaining: Array<{
    sub_item_id: number;
    remaining_quantity: number;
  }>;
} {
  const summary = calculateCoverageSummary(
    mainItemRequiredQuantity,
    subItemRequirements,
    packageCoverages
  );

  return {
    main_item_remaining: summary.main_item.remaining,
    subitem_remaining: summary.subitems
      .filter((si) => si.remaining > 0)
      .map((si) => ({
        sub_item_id: si.sub_item_id,
        remaining_quantity: si.remaining,
      })),
  };
}

