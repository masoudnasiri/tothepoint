# Custom Optimization Strategies for Your Procurement System

## 📋 Table of Contents
1. [Understanding Strategy Customization](#understanding-strategy-customization)
2. [Ready-to-Use Custom Strategies](#ready-to-use-custom-strategies)
3. [How to Implement Custom Strategies](#how-to-implement-custom-strategies)
4. [Strategy Templates by Business Scenario](#strategy-templates-by-business-scenario)
5. [Advanced Custom Strategies](#advanced-custom-strategies)

---

## Understanding Strategy Customization

### What is a Strategy?

A strategy defines **how to weight different factors** in the optimization objective function:

```python
# Basic formula
Minimize: Σ (cost × weight_factor)

# Where weight_factor depends on:
- Project priority
- Delivery urgency  
- Cash flow timing
- Supplier preferences
- Risk factors
```

### Current Built-in Strategies

| Strategy | Formula | Use Case |
|----------|---------|----------|
| **LOWEST_COST** | `cost × 1.0` | Pure cost minimization |
| **PRIORITY_WEIGHTED** | `cost × (11 - priority)` | Portfolio optimization |
| **FAST_DELIVERY** | `delivery_time` | Time-critical projects |
| **SMOOTH_CASHFLOW** | `cost × (1 + \|t - mid\| × 0.1)` | Cash flow management |
| **BALANCED** | `cost × (11-p) × 0.7 + time × 0.3` | Multi-criteria |

---

## Ready-to-Use Custom Strategies

### 🎯 Strategy 1: CASH_DISCOUNT_MAXIMIZER

**Goal:** Maximize cash discounts by preferring cash payment suppliers

**When to use:**
- You have good cash position
- Want to maximize early payment discounts
- Cash flow allows immediate payments

**Implementation:**

```python
# Add to optimization_engine_enhanced.py

class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    CASH_DISCOUNT_MAXIMIZER = "CASH_DISCOUNT_MAXIMIZER"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.CASH_DISCOUNT_MAXIMIZER:
    # Prefer cash payment options
    if option.payment_terms.get('type') == 'cash':
        discount_bonus = option.payment_terms.get('discount_percent', 0)
        # Reduce cost by discount bonus (makes it more attractive)
        weight = 1.0 - (discount_bonus / 100)
    else:
        # Penalize non-cash options
        weight = 1.2  # 20% penalty
```

**Expected Results:**
- Higher percentage of cash payment selections
- Lower total cost (due to discounts)
- Higher immediate cash outflow
- Reduced accounts payable

---

### 💰 Strategy 2: BUDGET_SMOOTHER

**Goal:** Minimize variance in budget usage across all time periods

**When to use:**
- Want predictable monthly spending
- Avoid end-of-period budget rushes
- Smooth resource allocation

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    BUDGET_SMOOTHER = "BUDGET_SMOOTHER"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.BUDGET_SMOOTHER:
    # Calculate target spending per period
    total_budget = sum(b.available_budget for b in self.budget_data.values())
    target_per_period = total_budget / len(self.budget_data)
    
    # Penalize deviations from target
    period_spending = self._calculate_period_spending(purchase_time)
    deviation = abs(period_spending - target_per_period)
    
    # Weight increases with deviation
    weight = 1.0 + (deviation / target_per_period) * 0.5
```

**Expected Results:**
- Even distribution of spending
- No budget spikes
- Predictable cash flow
- Easier financial planning

---

### 🏃 Strategy 3: CRITICAL_PATH_OPTIMIZER

**Goal:** Prioritize items on the critical path for early procurement

**When to use:**
- Project timelines are tight
- Dependencies between items
- Want to minimize project delays

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    CRITICAL_PATH_OPTIMIZER = "CRITICAL_PATH_OPTIMIZER"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.CRITICAL_PATH_OPTIMIZER:
    # Get critical path from dependency graph
    critical_path = self.get_critical_path()
    
    # Check if this item is on critical path
    item_id = f"P{project_id}_I{item_code}"
    is_critical = item_id in critical_path
    
    if is_critical:
        # Critical items: prioritize early delivery
        weight = delivery_time * 0.5  # Prefer early
    else:
        # Non-critical items: optimize for cost
        weight = 1.0
```

**Expected Results:**
- Critical path items procured first
- Non-critical items optimized for cost
- Reduced project completion time
- Better risk management

---

### 📦 Strategy 4: BULK_BUNDLING_MAXIMIZER

**Goal:** Maximize bundling discounts by grouping purchases

**When to use:**
- Suppliers offer volume discounts
- Want to reduce unit costs
- Can handle larger upfront payments

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    BULK_BUNDLING_MAXIMIZER = "BULK_BUNDLING_MAXIMIZER"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.BULK_BUNDLING_MAXIMIZER:
    # Check if bundling threshold is reachable
    if option.discount_bundle_threshold:
        threshold = option.discount_bundle_threshold
        current_qty = item.quantity
        
        if current_qty >= threshold:
            # Already at threshold - reward this
            weight = 0.8  # 20% bonus
        elif current_qty >= threshold * 0.8:
            # Close to threshold - incentivize
            weight = 0.9  # 10% bonus
        else:
            # Far from threshold - neutral
            weight = 1.0
    else:
        weight = 1.0
```

**Expected Results:**
- More bundling discount utilization
- Lower average unit costs
- Fewer suppliers (consolidation)
- Potential excess inventory

---

### 🔒 Strategy 5: SUPPLIER_DIVERSIFICATION

**Goal:** Avoid over-reliance on single suppliers (risk management)

**When to use:**
- Supply chain risk concerns
- Want supplier redundancy
- Regulatory compliance requires diversity

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    SUPPLIER_DIVERSIFICATION = "SUPPLIER_DIVERSIFICATION"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.SUPPLIER_DIVERSIFICATION:
    # Track selections per supplier
    supplier_count = self._count_supplier_selections(option.supplier_name)
    
    # Penalize over-concentration
    if supplier_count > 5:  # More than 5 items from same supplier
        penalty = (supplier_count - 5) * 0.1
        weight = 1.0 + penalty
    else:
        weight = 1.0
```

**Expected Results:**
- Broader supplier base
- Reduced single-supplier risk
- Potentially higher total cost
- Better negotiating position

---

### 🌍 Strategy 6: LOCAL_SUPPLIER_PREFERENCE

**Goal:** Prefer local/domestic suppliers over international

**When to use:**
- "Buy Local" initiatives
- Reduce shipping/lead time
- Support local economy
- Regulatory requirements

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    LOCAL_SUPPLIER_PREFERENCE = "LOCAL_SUPPLIER_PREFERENCE"

# First, add a field to ProcurementOption model:
# is_local = Column(Boolean, default=False)

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.LOCAL_SUPPLIER_PREFERENCE:
    # Assume we've added is_local field to options
    if hasattr(option, 'is_local') and option.is_local:
        # Give 15% cost advantage to local suppliers
        weight = 0.85
    else:
        # Standard weight for non-local
        weight = 1.0
```

**Expected Results:**
- Higher percentage of local suppliers
- Shorter lead times
- Slightly higher costs
- Reduced logistics complexity

---

### ⚖️ Strategy 7: RISK_ADJUSTED_OPTIMIZATION

**Goal:** Factor in supplier reliability/risk scores

**When to use:**
- Historical supplier performance data available
- Quality/reliability critical
- Risk-averse procurement

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    RISK_ADJUSTED_OPTIMIZATION = "RISK_ADJUSTED_OPTIMIZATION"

# First, add risk_score to ProcurementOption:
# risk_score = Column(Integer)  # 1-10, higher = riskier

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.RISK_ADJUSTED_OPTIMIZATION:
    # Get supplier risk score (1-10, where 10 = highest risk)
    risk_score = getattr(option, 'risk_score', 5)  # Default to medium
    
    # Penalize risky suppliers
    risk_penalty = (risk_score / 10) * 0.3  # Up to 30% penalty
    weight = 1.0 + risk_penalty
```

**Expected Results:**
- Preference for reliable suppliers
- Reduced procurement risk
- Potentially higher costs
- Fewer quality issues

---

### 🎯 Strategy 8: MULTI_YEAR_PLANNING

**Goal:** Optimize across longer time horizons with future considerations

**When to use:**
- Multi-year projects
- Long-term supplier agreements
- Strategic planning

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    MULTI_YEAR_PLANNING = "MULTI_YEAR_PLANNING"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.MULTI_YEAR_PLANNING:
    # Apply discount factor for future costs (time value of money)
    discount_rate = 0.05  # 5% annual discount rate
    years_ahead = delivery_time / 12  # Assuming monthly periods
    
    # Present value calculation
    discount_factor = 1 / ((1 + discount_rate) ** years_ahead)
    
    # Apply to cost
    weight = discount_factor
```

**Expected Results:**
- Future costs discounted appropriately
- Earlier purchases favored (NPV)
- Economically optimal timing
- Long-term cost minimization

---

### 💼 Strategy 9: PROJECT_DEADLINE_CRITICAL

**Goal:** Ensure all items for critical deadline projects arrive on time

**When to use:**
- Hard project deadlines
- Penalties for late delivery
- Time-sensitive projects

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    PROJECT_DEADLINE_CRITICAL = "PROJECT_DEADLINE_CRITICAL"

# First, add deadline to Project model:
# deadline_date = Column(Date, nullable=True)

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.PROJECT_DEADLINE_CRITICAL:
    project = self.projects.get(project_id)
    
    if hasattr(project, 'deadline_date') and project.deadline_date:
        # Calculate slack time (deadline - delivery)
        deadline_period = self._date_to_period(project.deadline_date)
        slack = deadline_period - delivery_time
        
        if slack < 2:  # Less than 2 periods slack
            # Very urgent - heavily penalize delays
            weight = delivery_time * 2.0
        elif slack < 5:
            # Moderately urgent
            weight = delivery_time * 1.5
        else:
            # Normal - optimize for cost
            weight = 1.0
    else:
        weight = 1.0
```

**Expected Results:**
- Deadline projects prioritized
- Reduced deadline violations
- Higher costs for urgent items
- Better schedule adherence

---

### 🔄 Strategy 10: QUARTERLY_ALIGNMENT

**Goal:** Align procurements with quarterly budget cycles

**When to use:**
- Quarterly budgeting process
- End-of-quarter spending targets
- Financial reporting alignment

**Implementation:**

```python
class OptimizationStrategy(str, Enum):
    # ... existing strategies ...
    QUARTERLY_ALIGNMENT = "QUARTERLY_ALIGNMENT"

# In _set_cpsat_objective method:
elif strategy == OptimizationStrategy.QUARTERLY_ALIGNMENT:
    # Determine which quarter (Q1, Q2, Q3, Q4)
    quarter = ((purchase_time - 1) // 3) + 1
    
    # Get quarterly budget target
    quarterly_budget = self._get_quarterly_budget(quarter)
    quarterly_spending = self._get_quarterly_spending(quarter)
    
    # If under budget, incentivize this quarter
    if quarterly_spending < quarterly_budget * 0.9:
        weight = 0.95  # 5% incentive
    elif quarterly_spending > quarterly_budget * 1.1:
        weight = 1.10  # 10% penalty (over budget)
    else:
        weight = 1.0
```

**Expected Results:**
- Balanced quarterly spending
- Better budget utilization
- Reduced budget carryover
- Improved financial reporting

---

## How to Implement Custom Strategies

### Step 1: Add Strategy to Enum

Edit `backend/app/optimization_engine_enhanced.py`:

```python
class OptimizationStrategy(str, Enum):
    """Optimization strategies for multi-proposal generation"""
    LOWEST_COST = "LOWEST_COST"
    BALANCED = "BALANCED"
    SMOOTH_CASHFLOW = "SMOOTH_CASHFLOW"
    PRIORITY_WEIGHTED = "PRIORITY_WEIGHTED"
    FAST_DELIVERY = "FAST_DELIVERY"
    
    # ADD YOUR CUSTOM STRATEGY HERE
    YOUR_CUSTOM_STRATEGY = "YOUR_CUSTOM_STRATEGY"
```

### Step 2: Implement Strategy Logic

In the same file, add logic to `_set_cpsat_objective` method:

```python
def _set_cpsat_objective(self, model: cp_model.CpModel, variables: Dict, strategy: OptimizationStrategy):
    """Set objective function for CP-SAT based on strategy"""
    objective_terms = []
    
    for var_name, var in variables.items():
        # ... extract variables ...
        
        # ADD YOUR STRATEGY HERE
        if strategy == OptimizationStrategy.YOUR_CUSTOM_STRATEGY:
            # Your custom weighting logic
            weight = self._calculate_your_custom_weight(
                option, item, project, delivery_time
            )
        elif strategy == OptimizationStrategy.LOWEST_COST:
            weight = 1.0
        # ... rest of strategies ...
```

### Step 3: Add to Solver Info

Edit `backend/app/routers/finance.py`:

```python
"available_strategies": [
    # ... existing strategies ...
    {
        "type": "YOUR_CUSTOM_STRATEGY",
        "name": "Your Custom Strategy Name",
        "description": "Brief description",
        "objective": "What it optimizes for"
    }
]
```

### Step 4: Test Your Strategy

```python
# Test with single strategy
optimizer = EnhancedProcurementOptimizer(db, SolverType.CP_SAT)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=False,
    strategies=[OptimizationStrategy.YOUR_CUSTOM_STRATEGY]
)
```

---

## Strategy Templates by Business Scenario

### Scenario 1: Startup / Cash-Constrained

**Priorities:**
- Minimize cash outflow
- Spread payments
- Maximize credit terms

**Recommended Strategy:**
```python
# INSTALLMENT_MAXIMIZER
# Prefer payment terms with installments

if option.payment_terms.get('type') == 'installments':
    weight = 0.8  # 20% preference
else:
    weight = 1.0
```

---

### Scenario 2: Established Company / Cost Focus

**Priorities:**
- Lowest total cost
- Quality suppliers
- Bulk discounts

**Recommended Strategy:**
```python
# COST_QUALITY_BALANCED
# 80% cost, 20% quality/risk

cost_weight = 0.8
risk_penalty = (option.risk_score / 10) * 0.2
weight = cost_weight + risk_penalty
```

---

### Scenario 3: Fast-Growing / Time Critical

**Priorities:**
- Fast delivery
- Reliable suppliers
- Avoid stockouts

**Recommended Strategy:**
```python
# SPEED_RELIABILITY
# Minimize delivery time + penalize risky suppliers

time_factor = delivery_time * 0.7
risk_factor = (option.risk_score / 10) * 0.3
weight = time_factor + risk_factor
```

---

### Scenario 4: Government / Compliance

**Priorities:**
- Local suppliers
- Certified suppliers
- Transparent pricing

**Recommended Strategy:**
```python
# COMPLIANCE_OPTIMIZER
# Prefer certified local suppliers

if option.is_local and option.is_certified:
    weight = 0.7  # 30% preference
elif option.is_local or option.is_certified:
    weight = 0.85  # 15% preference
else:
    weight = 1.0
```

---

## Advanced Custom Strategies

### Strategy: MACHINE_LEARNING_PREDICTED

**Goal:** Use ML to predict best suppliers based on historical performance

```python
class OptimizationStrategy(str, Enum):
    ML_PREDICTED = "ML_PREDICTED"

# In objective function:
elif strategy == OptimizationStrategy.ML_PREDICTED:
    # Load pre-trained model
    predicted_score = self.ml_model.predict_supplier_performance(
        supplier=option.supplier_name,
        item_code=item_code,
        quantity=item.quantity
    )
    
    # Use prediction as weight
    # Higher score = better supplier
    weight = 1.0 / (predicted_score + 0.1)
```

---

### Strategy: MONTE_CARLO_RISK

**Goal:** Factor in uncertainty using Monte Carlo simulation

```python
class OptimizationStrategy(str, Enum):
    MONTE_CARLO_RISK = "MONTE_CARLO_RISK"

# In objective function:
elif strategy == OptimizationStrategy.MONTE_CARLO_RISK:
    # Simulate cost scenarios
    scenarios = []
    for _ in range(100):
        simulated_cost = self._simulate_cost_scenario(option, item)
        scenarios.append(simulated_cost)
    
    # Use 95th percentile as risk-adjusted cost
    risk_adjusted_cost = np.percentile(scenarios, 95)
    
    # Weight based on risk-adjusted cost
    weight = risk_adjusted_cost / cost
```

---

## Testing Your Custom Strategy

### Test Checklist

- [ ] Strategy added to enum
- [ ] Logic implemented in objective function
- [ ] Added to solver-info endpoint
- [ ] Tested with small dataset
- [ ] Compared results with built-in strategies
- [ ] Documented strategy purpose
- [ ] Added to frontend (optional)

### Test Script

```python
# test_custom_strategy.py

async def test_custom_strategy():
    async with async_session_maker() as db:
        optimizer = EnhancedProcurementOptimizer(db, SolverType.CP_SAT)
        
        request = OptimizationRunRequest(
            max_time_slots=12,
            time_limit_seconds=60
        )
        
        # Test your custom strategy
        result = await optimizer.run_optimization(
            request,
            generate_multiple_proposals=False,
            strategies=[OptimizationStrategy.YOUR_CUSTOM_STRATEGY]
        )
        
        print(f"Status: {result.status}")
        print(f"Total Cost: ${result.total_cost}")
        print(f"Items: {result.items_optimized}")

asyncio.run(test_custom_strategy())
```

---

## Summary: Choosing the Right Strategy

| Your Situation | Recommended Custom Strategy |
|---------------|----------------------------|
| **Limited cash** | INSTALLMENT_MAXIMIZER |
| **Need reliability** | RISK_ADJUSTED_OPTIMIZATION |
| **Project deadlines** | PROJECT_DEADLINE_CRITICAL |
| **Cost focus** | BULK_BUNDLING_MAXIMIZER |
| **Cash flow mgmt** | BUDGET_SMOOTHER |
| **Risk management** | SUPPLIER_DIVERSIFICATION |
| **Local preference** | LOCAL_SUPPLIER_PREFERENCE |
| **Multi-year** | MULTI_YEAR_PLANNING |
| **Quarterly budgets** | QUARTERLY_ALIGNMENT |
| **Critical path** | CRITICAL_PATH_OPTIMIZER |

---

## 🎯 Recommended Action Plan

1. **Week 1:** Use built-in strategies to understand your problem
2. **Week 2:** Identify which custom strategy fits your needs
3. **Week 3:** Implement and test custom strategy
4. **Week 4:** Run parallel comparisons (built-in vs. custom)
5. **Week 5:** Deploy custom strategy to production

---

**Your procurement optimization is now fully customizable to your exact business needs! 🚀**

