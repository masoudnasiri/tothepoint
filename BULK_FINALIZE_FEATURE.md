# Bulk Finalize/Unfinalize Feature

## Overview
Added a **"Finalize All" / "Unfinalize All"** button for each item to quickly toggle the finalization status of all procurement options for that item.

## Features

### 1. **Smart Toggle Button**
The button automatically changes based on the current state of options:

#### When NOT all options are finalized:
- **Button**: Green "Finalize All" with ✓✓ icon
- **Action**: Marks all options for that item as finalized
- **Use Case**: After reviewing all suppliers, finalize them all at once

#### When ALL options are finalized:
- **Button**: Orange outlined "Unfinalize All" with ✗✓ icon  
- **Action**: Marks all options for that item as draft
- **Use Case**: Need to re-evaluate suppliers or add more options

### 2. **Confirmation Dialog**
- Shows confirmation before bulk action
- Displays count of options that will be affected
- Example: "Are you sure you want to finalize all 5 options for ELEC001?"

### 3. **Visual Feedback**
- Button changes color and icon based on state
- Success/error messages after action
- Table updates immediately to show new status

## User Interface

### Button Location
Located next to "Add Option" button for each item:
```
[Add Option for ELEC001]  [Finalize All]
```

### Button States

| All Finalized? | Button Text | Color | Icon | Action |
|----------------|-------------|-------|------|--------|
| ❌ No | Finalize All | Green (contained) | ✓✓ | Finalize all |
| ✅ Yes | Unfinalize All | Orange (outlined) | ✗✓ | Unfinalize all |

## Usage Examples

### Example 1: Finalize All Options
**Scenario**: You've added 5 suppliers for ELEC001 and reviewed them all

1. Expand ELEC001 accordion
2. See 5 options with "Draft" status
3. Click **"Finalize All"** button (green)
4. Confirm dialog: "Are you sure you want to finalize all 5 options for ELEC001?"
5. Click "OK"
6. ✅ All 5 options now show "Finalized" status
7. Button changes to **"Unfinalize All"** (orange)

### Example 2: Unfinalize All Options
**Scenario**: Need to re-evaluate suppliers or add more options

1. Expand ELEC001 accordion
2. See 5 options with "Finalized" status
3. Click **"Unfinalize All"** button (orange)
4. Confirm dialog: "Are you sure you want to unfinalize all 5 options for ELEC001?"
5. Click "OK"
6. ✅ All 5 options now show "Draft" status
7. Button changes to **"Finalize All"** (green)

### Example 3: Mixed Status
**Scenario**: Some options finalized, some draft

1. Expand ELEC001 accordion
2. See 3 finalized, 2 draft options
3. Button shows **"Finalize All"** (green) - because not ALL are finalized
4. Click button to finalize the remaining 2 draft options
5. ✅ All 5 options now finalized

## Technical Implementation

### Frontend Changes
**File**: `frontend/src/pages/ProcurementPage.tsx`

#### New Handler Function
```typescript
const handleBulkFinalizeToggle = async (itemCode: string, shouldFinalize: boolean) => {
  const itemOptions = procurementOptions.filter(opt => opt.item_code === itemCode);
  
  if (itemOptions.length === 0) return;
  
  const action = shouldFinalize ? 'finalize' : 'unfinalize';
  if (!window.confirm(`Are you sure you want to ${action} all ${itemOptions.length} options for ${itemCode}?`)) {
    return;
  }
  
  try {
    // Update all options for this item
    const updatePromises = itemOptions.map(option => 
      procurementAPI.update(option.id, { is_finalized: shouldFinalize })
    );
    
    await Promise.all(updatePromises);
    
    // Refresh data
    await fetchData();
    
    setError('');
  } catch (err: any) {
    setError(err.response?.data?.detail || `Failed to ${action} options`);
  }
};
```

#### Button Component
```tsx
{itemOptions.length > 0 && (() => {
  const allFinalized = itemOptions.every((opt: any) => opt.is_finalized);
  return (
    <Button
      variant={allFinalized ? "outlined" : "contained"}
      color={allFinalized ? "warning" : "success"}
      startIcon={allFinalized ? <RemoveDoneIcon /> : <DoneAllIcon />}
      onClick={() => handleBulkFinalizeToggle(itemCode, !allFinalized)}
    >
      {allFinalized ? 'Unfinalize All' : 'Finalize All'}
    </Button>
  );
})()}
```

### New Icons Imported
```typescript
import {
  DoneAll as DoneAllIcon,      // ✓✓ for Finalize All
  RemoveDone as RemoveDoneIcon, // ✗✓ for Unfinalize All
} from '@mui/icons-material';
```

## Benefits

### 1. **Time Saving**
- No need to manually check/uncheck each option
- One click to finalize multiple options
- Especially useful for items with many suppliers

### 2. **Workflow Efficiency**
- Quick batch operations
- Easy to finalize after review session
- Simple to unfinalize for re-evaluation

### 3. **Clear Visual State**
- Button shows current state at a glance
- Color coding (green = action needed, orange = already done)
- Immediate feedback after action

### 4. **Safety**
- Confirmation dialog prevents accidents
- Shows count of affected options
- Can cancel before applying

## Workflow Integration

### Typical Procurement Workflow

1. **Add Options Phase**
   - Add multiple supplier options for each item
   - All start as "Draft"
   - Button shows "Finalize All" (green)

2. **Review Phase**
   - Review supplier details
   - Compare prices and terms
   - Edit options as needed

3. **Finalization Phase**
   - Click **"Finalize All"** for each item
   - Confirm bulk action
   - Options ready for optimization

4. **Optimization Phase**
   - Run procurement optimization
   - Only finalized options are used
   - Get optimal supplier selection

5. **Re-evaluation Phase** (if needed)
   - Click **"Unfinalize All"**
   - Add new suppliers or update prices
   - Re-finalize when ready

## Testing Checklist

- [x] Button appears for each item with options
- [x] Button shows "Finalize All" when not all finalized
- [x] Button shows "Unfinalize All" when all finalized
- [x] Confirmation dialog shows correct count
- [x] All options update after confirmation
- [x] Button state updates after action
- [x] Table status chips update correctly
- [x] Works with single option
- [x] Works with multiple options
- [x] Error handling for failed updates

## Next Steps

1. **Refresh your browser** (Ctrl+Shift+R)
2. Go to **Procurement** page
3. Expand any item with options
4. You'll see the new **"Finalize All"** or **"Unfinalize All"** button
5. Try it out - it will bulk update all options for that item!

## Files Modified
- `frontend/src/pages/ProcurementPage.tsx` - Added bulk finalize functionality
- Frontend service restarted

## Status
✅ **Feature is now LIVE!**

