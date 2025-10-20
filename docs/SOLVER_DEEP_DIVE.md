# Deep Dive: OR-Tools Solvers Explained

## Table of Contents
1. [CP-SAT Solver](#cp-sat-solver)
2. [GLOP Solver](#glop-solver)
3. [SCIP Solver](#scip-solver)
4. [CBC Solver](#cbc-solver)
5. [Comparison Matrix](#comparison-matrix)
6. [When to Use Each Solver](#when-to-use-each-solver)

---

## CP-SAT Solver

### 🎯 Full Name
**Constraint Programming with SAT (Boolean Satisfiability)**

### 📖 What Is It?

CP-SAT is Google's state-of-the-art constraint programming solver that uses **SAT (Boolean Satisfiability)** techniques under the hood. It's designed to solve **constraint satisfaction and optimization problems** with complex logical relationships.

### 🔧 How It Works

**1. Model Construction:**
```python
model = cp_model.CpModel()

# Create variables
x = model.NewBoolVar('x')  # Binary variable
y = model.NewIntVar(0, 10, 'y')  # Integer variable

# Add constraints
model.Add(x + y <= 5)  # Linear constraint
model.AddBoolOr([x, y > 3])  # Logical constraint
```

**2. Constraint Propagation:**
- Reduces variable domains based on constraints
- Eliminates impossible combinations early
- Uses sophisticated propagation algorithms

**3. Search Strategy:**
- Uses Conflict-Driven Clause Learning (CDCL)
- Learns from failures
- Backtracking with intelligent clause learning

**4. Solution Finding:**
- Explores search tree efficiently
- Prunes branches that can't lead to better solutions
- Guarantees optimality (if time permits)

### 💪 Strengths

**1. Handles Complex Constraints Naturally**
```python
# Example: "If we buy from supplier A, we must also buy item X"
model.AddImplication(buy_supplier_A, buy_item_X)

# Example: "Total quantity must be exactly divisible by pack size"
model.AddModuloEquality(0, total_quantity, pack_size)
```

**2. Non-Linear Relationships**
```python
# Bundling discounts (non-linear)
if quantity >= threshold:
    cost = base_cost * (1 - discount_percent)
```

**3. Logical Conditions**
```python
# All-or-nothing constraints
model.AddBoolOr([var1, var2, var3])  # At least one must be true
model.AddBoolAnd([var1, var2])  # Both must be true
```

**4. Automatically Handles Integer Variables**
- No LP relaxation needed
- True integer solutions
- No rounding issues

### ⚡ Performance Characteristics

**Time Complexity:**
- Worst case: Exponential O(2^n)
- In practice: Much better due to:
  - Constraint propagation
  - Clause learning
  - Smart search strategies

**Space Complexity:**
- O(n × m) where n = variables, m = constraints
- Efficient memory usage
- Can handle medium-sized problems (100-1000 variables)

**Typical Performance (Your System):**
```
50 items, 10 options each, 12 time slots = ~6,000 variables
Expected time: 15-45 seconds
Solution quality: OPTIMAL
```

### 🎯 Best Use Cases in Your System

**1. Complex Bundling Rules**
```python
# If quantity >= 100, discount applies to ALL units
# CP-SAT handles this naturally without linearization
```

**2. Payment Term Dependencies**
```python
# If payment is cash, must use specific suppliers
# Logical constraints are CP-SAT's strength
```

**3. Project Dependencies**
```python
# Item B can only be ordered after Item A is delivered
# Time-based dependencies handled well
```

**4. Capacity Constraints**
```python
# Supplier can handle max 5 items per period
# Resource constraints with CP-SAT
```

### ⚙️ Configuration Options

```python
solver = cp_model.CpSolver()

# Time limit
solver.parameters.max_time_in_seconds = 300

# Parallelism
solver.parameters.num_search_workers = 8  # Use 8 cores

# Optimization focus
solver.parameters.linearization_level = 2  # More aggressive

# Preprocessing
solver.parameters.cp_model_presolve = True  # Enable preprocessing

# Logging
solver.parameters.log_search_progress = True
```

### 📊 Real-World Example

**Your Procurement Scenario:**
```python
# Problem: 100 items, 5 procurement options each, 12 time periods
# Variables: 100 × 5 × 12 = 6,000 binary variables

# Constraints:
# - Each item procured exactly once
# - Budget limits per period
# - Lead times respected
# - Priority weights applied

# CP-SAT Solution:
# Time: 25-45 seconds
# Status: OPTIMAL
# Quality: True optimal solution
```

---

## GLOP Solver

### 🎯 Full Name
**Google Linear Optimization Package**

### 📖 What Is It?

GLOP is Google's **Linear Programming (LP)** solver. It solves problems where:
- Objective is linear
- All constraints are linear
- Variables can be continuous

For integer problems (like yours), GLOP uses **LP relaxation** then rounds.

### 🔧 How It Works

**1. LP Relaxation:**
```python
# Instead of: x ∈ {0, 1} (binary)
# GLOP uses: 0 ≤ x ≤ 1 (continuous)

# This makes the problem much easier to solve!
```

**2. Simplex Algorithm:**
```
Start at feasible corner point
  ↓
Check adjacent corner points
  ↓
Move to better corner point
  ↓
Repeat until optimal corner found
```

**3. Dual Simplex:**
- Maintains dual feasibility
- Works from outside feasible region
- Often faster for constraint-heavy problems

**4. Rounding (for Integer Solutions):**
```python
# After solving LP relaxation
if x.solution_value() > 0.5:
    x_integer = 1
else:
    x_integer = 0
```

### 💪 Strengths

**1. Extreme Speed**
```python
# Same problem as CP-SAT
# GLOP: 3-8 seconds
# CP-SAT: 25-45 seconds
# Speedup: 5-10x faster! 🚀
```

**2. Scales to Large Problems**
```
1,000 items: CP-SAT struggles, GLOP handles easily
10,000 items: CP-SAT times out, GLOP still works
```

**3. Predictable Performance**
```
O(n³) time complexity (polynomial!)
Much better than CP-SAT's exponential worst case
```

**4. Low Memory Usage**
```
Uses less memory than CP-SAT
Can handle larger problems on same hardware
```

### ⚡ Performance Characteristics

**Time Complexity:**
- Average: O(n² × m) to O(n³)
- n = variables, m = constraints
- Polynomial, not exponential!

**Space Complexity:**
- O(n × m) for constraint matrix
- Very efficient

**Typical Performance (Your System):**
```
50 items, 10 options each, 12 time slots = ~6,000 variables
Expected time: 3-8 seconds ⚡
Solution quality: Good (LP relaxation + rounding)
```

### ⚠️ Limitations

**1. Not Truly Optimal for Integer Problems**
```python
# True optimal: Select options A, B, C → Total cost $10,000
# GLOP rounded: Select options A, B, D → Total cost $10,050
# Gap: 0.5% (usually acceptable)
```

**2. Can't Handle Complex Logic**
```python
# CP-SAT can do:
model.AddImplication(x, y)

# GLOP can't directly handle:
# - If-then constraints
# - All-or-nothing
# - Complex bundling
```

**3. Requires Linearization**
```python
# Non-linear: cost = base_cost × (1 - discount)^quantity
# Must linearize for GLOP (may lose some accuracy)
```

### 🎯 Best Use Cases in Your System

**1. Quick Feasibility Checks**
```python
# "Can I procure everything within budget?"
# GLOP answers in 5 seconds instead of 30
```

**2. Large-Scale Procurement**
```python
# 500+ items across 20 projects
# GLOP handles, CP-SAT times out
```

**3. Initial Exploration**
```python
# Day 1: Run GLOP to understand problem
# Day 2: Refine with CP-SAT if needed
```

**4. Production Speed Requirements**
```python
# Need results in < 10 seconds?
# GLOP is your solver
```

### ⚙️ Configuration Options

```python
solver = pywraplp.Solver.CreateSolver('GLOP')

# Time limit (milliseconds)
solver.SetTimeLimit(60000)  # 60 seconds

# Solution precision
solver.set_parameters("solution_feasibility_tolerance", 1e-6)

# Algorithm choice
# GLOP automatically chooses between:
# - Primal Simplex
# - Dual Simplex
# - Barrier method
```

### 📊 Real-World Example

**Your Procurement Scenario:**
```python
# Problem: 100 items, 5 options each, 12 periods
# LP Relaxation: 6,000 continuous variables

# Linear constraints:
# - Budget: Σ(cost × quantity) ≤ budget_limit
# - Demand: Σ(selection_vars) = 1 per item

# GLOP Solution:
# Time: 5-8 seconds ⚡
# Status: OPTIMAL (for LP relaxation)
# After rounding: FEASIBLE (99% as good as true optimal)
```

---

## SCIP Solver

### 🎯 Full Name
**Solving Constraint Integer Programs**

### 📖 What Is It?

SCIP is an **academic/research** Mixed-Integer Programming (MIP) solver developed at Zuse Institute Berlin. It's one of the fastest **non-commercial** MIP solvers in the world.

### 🔧 How It Works

**1. Branch-and-Bound:**
```
Problem
├─ Branch 1 (x=0)
│  ├─ Bound: LP relaxation
│  └─ Branch further if needed
└─ Branch 2 (x=1)
   ├─ Bound: LP relaxation
   └─ Prune if worse than best found
```

**2. Cutting Planes:**
```python
# Add additional constraints that:
# - Don't eliminate any integer solutions
# - Tighten the LP relaxation
# - Make problem easier to solve

# Example: Gomory cuts, Cover cuts, etc.
```

**3. Presolving:**
```python
# Before solving:
# - Eliminate redundant constraints
# - Fix variables with forced values
# - Strengthen bounds
# - Reduce problem size
```

**4. Heuristics:**
```python
# Use fast heuristics to find good solutions quickly:
# - Rounding heuristics
# - Diving heuristics
# - Local search
```

### 💪 Strengths

**1. State-of-the-Art Algorithms**
```python
# Implements cutting-edge research
# Over 100 types of cutting planes
# Advanced branching strategies
```

**2. Excellent for Research**
```python
# Detailed statistics
# Customizable at every level
# Plugin architecture
# Perfect for academic work
```

**3. Free for Academic Use**
```python
# No cost for universities
# Open architecture
# Extensive documentation
```

**4. Very Configurable**
```python
# Over 1,000 parameters
# Can tune for specific problem types
# Disable/enable specific features
```

### ⚡ Performance Characteristics

**Time Complexity:**
- Worst case: Exponential
- In practice: Better than naive branch-and-bound
- Similar to commercial solvers for many problems

**Typical Performance (Your System):**
```
50 items, 10 options, 12 periods = ~6,000 binary variables
Expected time: 30-60 seconds
Solution quality: OPTIMAL
Comparison: Similar to CP-SAT, slower than GLOP
```

### ⚠️ Licensing Considerations

**Academic Use: ✅ FREE**
```
- Universities
- Research institutions
- Non-commercial projects
```

**Commercial Use: ⚠️ Requires ZIB Academic License**
```
- May require license fee
- Check ZIB website for details
- Alternative: Use CBC (fully open-source)
```

### 🎯 Best Use Cases in Your System

**1. Research and Analysis**
```python
# Studying different formulations
# Benchmarking optimization approaches
# Academic papers
```

**2. When Commercial Solvers Unavailable**
```python
# Best free MIP solver
# Alternative to Gurobi/CPLEX
```

**3. Custom Algorithm Development**
```python
# Plugin your own heuristics
# Custom branching rules
# Research on optimization methods
```

### 📊 Real-World Example

**Your Procurement Scenario:**
```python
# Problem: 100 items, 5 options, 12 periods

# SCIP Solution:
# Time: 40-70 seconds
# Status: OPTIMAL
# Quality: True optimal (like CP-SAT)
# Use case: Research on procurement optimization
```

---

## CBC Solver

### 🎯 Full Name
**Coin-or Branch and Cut**

### 📖 What Is It?

CBC is an **open-source** Mixed-Integer Programming solver from the COIN-OR project. It's **production-ready**, **fully free**, and used by many commercial applications.

### 🔧 How It Works

**1. Branch-and-Cut:**
```
Same as branch-and-bound, but:
  + Cutting planes at each node
  + More aggressive preprocessing
  + Better dual bounds
```

**2. Advanced Preprocessing:**
```python
# CBC's strong preprocessing:
# - Probing (test variable assignments)
# - Coefficient strengthening
# - Constraint aggregation
```

**3. Multiple Heuristics:**
```python
# CBC runs several heuristics:
# - Feasibility pump
# - RINS (Relaxation Induced Neighborhood Search)
# - Local search
# - Diving heuristics
```

**4. Parallel Processing:**
```python
# Can use multiple threads
# Parallel tree search
# Concurrent heuristics
```

### 💪 Strengths

**1. Completely Open-Source**
```python
# EPL (Eclipse Public License)
# No licensing worries
# Commercial use: ✅ FREE
# No restrictions
```

**2. Production-Ready**
```python
# Used in real commercial applications
# Stable and well-tested
# Long track record
```

**3. Good Performance**
```python
# Not as fast as Gurobi/CPLEX
# But competitive with SCIP
# Much faster than naive branch-and-bound
```

**4. Active Community**
```python
# Part of COIN-OR project
# Regular updates
# Good documentation
# Community support
```

### ⚡ Performance Characteristics

**Time Complexity:**
- Exponential worst case
- Good practical performance
- Effective preprocessing helps

**Typical Performance (Your System):**
```
50 items, 10 options, 12 periods = ~6,000 binary variables
Expected time: 20-40 seconds
Solution quality: OPTIMAL
Sweet spot: Production MIP problems
```

### 🎯 Best Use Cases in Your System

**1. Production Deployment**
```python
# When you need:
# - True optimal solutions
# - No licensing concerns
# - Reliable performance
# → CBC is perfect
```

**2. Commercial Applications**
```python
# Selling your procurement system?
# CBC has no licensing fees
# Deploy freely
```

**3. Medium-to-Large Problems**
```python
# 100-500 items: CBC handles well
# Faster than CP-SAT for pure MIP
# More reliable than GLOP for integers
```

**4. Standard MIP Formulations**
```python
# Linear constraints
# Integer variables
# Linear objective
# → CBC excels
```

### ⚙️ Configuration Options

```python
solver = pywraplp.Solver.CreateSolver('CBC')

# Time limit
solver.SetTimeLimit(120000)  # 120 seconds

# Number of threads
solver.SetNumThreads(4)

# MIP gap tolerance (stop when within X% of optimal)
solver.SetSolverSpecificParametersAsString("ratioGap:0.01")

# Emphasis
solver.SetSolverSpecificParametersAsString("seconds:120")
```

### 📊 Real-World Example

**Your Procurement Scenario:**
```python
# Problem: 100 items, 5 options, 12 periods

# CBC Solution:
# Time: 25-35 seconds
# Status: OPTIMAL
# Quality: True optimal
# Use case: Production procurement optimization

# Why CBC?
# ✅ Open-source (no licensing)
# ✅ Production-ready
# ✅ Good performance
# ✅ Reliable results
```

---

## Comparison Matrix

### Performance Comparison

| Metric | CP-SAT | GLOP | SCIP | CBC |
|--------|--------|------|------|-----|
| **Speed (50 items)** | 25-45s | 3-8s ⚡ | 35-60s | 20-35s |
| **Speed (500 items)** | Timeout | 15-30s ⚡ | 180-300s | 120-200s |
| **Solution Quality** | Optimal ⭐ | Good | Optimal ⭐ | Optimal ⭐ |
| **Memory Usage** | Medium | Low ⭐ | Medium | Medium |
| **Scalability** | Medium | High ⭐ | Medium | High |

### Feature Comparison

| Feature | CP-SAT | GLOP | SCIP | CBC |
|---------|--------|------|------|-----|
| **Complex Constraints** | ✅ Excellent | ❌ Limited | ✅ Good | ✅ Good |
| **Integer Variables** | ✅ Native | ⚠️ Rounded | ✅ Native | ✅ Native |
| **Linear Problems** | ✅ Good | ✅ Excellent | ✅ Good | ✅ Good |
| **Non-Linear** | ✅ Some | ❌ No | ❌ No | ❌ No |
| **Logical Constraints** | ✅ Excellent | ❌ No | ⚠️ Limited | ⚠️ Limited |

### Licensing Comparison

| Solver | License | Commercial Use | Cost |
|--------|---------|----------------|------|
| **CP-SAT** | Apache 2.0 | ✅ Free | $0 |
| **GLOP** | Apache 2.0 | ✅ Free | $0 |
| **SCIP** | ZIB Academic | ⚠️ License needed | Contact ZIB |
| **CBC** | EPL | ✅ Free | $0 |

---

## When to Use Each Solver

### Decision Flowchart

```
Start: What's your priority?
│
├─ SPEED is critical
│  └─ Use GLOP
│     - 5-10x faster than others
│     - Accepts ~1% optimality gap
│
├─ TRUE OPTIMALITY required
│  ├─ Problem has complex constraints?
│  │  └─ Use CP-SAT
│  │     - Handles logic naturally
│  │     - Best for constraint-heavy
│  │
│  └─ Standard MIP problem?
│     ├─ Commercial deployment?
│     │  └─ Use CBC
│     │     - No licensing issues
│     │     - Production-ready
│     │
│     └─ Research/Academic?
│        └─ Use SCIP
│           - Best for research
│           - Highly configurable
│
└─ EXPLORATION phase
   └─ Use CP-SAT with multiple strategies
      - Most flexible
      - Compare all approaches
```

### Recommendation by Problem Size

**Small (< 50 items):**
```
1st choice: CP-SAT (fast enough, most flexible)
2nd choice: CBC (if pure MIP)
```

**Medium (50-500 items):**
```
1st choice: CBC (best balance)
2nd choice: CP-SAT (if complex constraints)
3rd choice: GLOP (if speed critical)
```

**Large (500+ items):**
```
1st choice: GLOP (only one fast enough)
2nd choice: CBC (if must be optimal)
```

### Recommendation by Use Case

**Development/Testing:**
```
Use: CP-SAT with multiple proposals
Why: See all options, understand trade-offs
```

**Production/Daily Use:**
```
Use: CBC with single strategy
Why: Reliable, fast, no licensing
```

**Quick Checks:**
```
Use: GLOP
Why: 10x faster, good enough
```

**Research:**
```
Use: SCIP or CP-SAT
Why: Most configurable, detailed stats
```

---

## Practical Examples for Your System

### Example 1: Small Daily Run (30 items)

**Best Solver: CP-SAT**
```python
optimizer = EnhancedProcurementOptimizer(db, SolverType.CP_SAT)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=True  # Compare strategies
)
# Time: 15-25 seconds
# Quality: OPTIMAL
```

### Example 2: Large Quarterly Planning (300 items)

**Best Solver: CBC**
```python
optimizer = EnhancedProcurementOptimizer(db, SolverType.CBC)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=False,  # Single strategy for speed
    strategies=[OptimizationStrategy.PRIORITY_WEIGHTED]
)
# Time: 60-90 seconds
# Quality: OPTIMAL
```

### Example 3: Quick Feasibility Check

**Best Solver: GLOP**
```python
optimizer = EnhancedProcurementOptimizer(db, SolverType.GLOP)
request.time_limit_seconds = 30  # Quick
result = await optimizer.run_optimization(request)
# Time: 5-10 seconds
# Quality: Good enough for feasibility
```

### Example 4: Research Analysis

**Best Solver: SCIP**
```python
optimizer = EnhancedProcurementOptimizer(db, SolverType.SCIP)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=True,
    strategies=list(OptimizationStrategy)  # All strategies
)
# Time: 3-5 minutes
# Quality: OPTIMAL with detailed stats
```

---

## Summary

| Your Need | Best Solver | Why |
|-----------|-------------|-----|
| **First time using** | CP-SAT | Most flexible, see all options |
| **Daily production** | CBC | Fast, reliable, no licensing |
| **Quick check** | GLOP | 10x faster |
| **Complex rules** | CP-SAT | Handles logic best |
| **Large scale (500+)** | GLOP | Only one fast enough |
| **Research** | SCIP | Most configurable |
| **Commercial product** | CBC | Fully open-source |

**My recommendation for you: Start with CP-SAT to learn, then switch to CBC for production! 🚀**

