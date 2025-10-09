# OR-Tools Enhanced Optimization Guide

## Overview

Your Procurement Decision Support System now supports **multiple OR-Tools solvers** with **advanced optimization strategies**. This guide will help you understand when and how to use each solver and strategy to get the best results for your procurement planning.

---

## 🚀 Quick Start

### For First-Time Users

1. **Use CP-SAT with Multiple Proposals**
   - Go to Optimization page
   - Select `CP_SAT` solver
   - Enable "Generate Multiple Proposals"
   - Click "Run Optimization"
   - Review all proposals and select the best one

2. **For Production Use**
   - After testing different strategies, select your preferred solver and strategy
   - Use single-strategy mode for faster execution
   - Lock decisions when ready

---

## 📊 Available Solvers

### 1. CP-SAT (Constraint Programming SAT)

**Type:** Constraint Programming  
**Best For:** Complex constraints, non-linear relationships, logical conditions

#### When to Use:
- ✅ You have complex business rules and constraints
- ✅ Relationships between variables are non-linear
- ✅ You need to handle logical conditions (if-then rules)
- ✅ Medium-sized problems (up to 1000 items)
- ✅ You want the most flexible solver

#### Advantages:
- Handles very complex constraints naturally
- Excellent at finding optimal solutions for constraint-heavy problems
- No need to linearize your problem
- Built-in support for many constraint types

#### Example Use Cases:
```
- Items with bundling discounts (non-linear cost structure)
- Complex payment term combinations
- Dependencies between project items
- Supplier capacity constraints
```

#### Configuration Example:
```json
{
  "solver_type": "CP_SAT",
  "max_time_slots": 12,
  "time_limit_seconds": 300,
  "generate_multiple_proposals": true
}
```

---

### 2. GLOP (Google Linear Optimizer)

**Type:** Linear Programming  
**Best For:** Pure linear problems, very large-scale optimization

#### When to Use:
- ✅ All costs and constraints are linear
- ✅ Very large problems (1000+ items)
- ✅ You need the fastest possible solution
- ✅ You can tolerate LP relaxation with rounding

#### Advantages:
- **Extremely fast** for linear problems
- Scales to very large problem sizes
- Efficient memory usage
- Mature and well-tested algorithm

#### Limitations:
- ⚠️ Requires all constraints to be linear
- ⚠️ Uses LP relaxation then rounds to integers (may not be truly optimal)
- ⚠️ Cannot handle complex logical constraints directly

#### Example Use Cases:
```
- Simple cost minimization across many items
- Budget allocation without complex rules
- Large-scale procurement with linear pricing
- Fast initial feasibility checks
```

#### Configuration Example:
```json
{
  "solver_type": "GLOP",
  "max_time_slots": 24,
  "time_limit_seconds": 120,
  "generate_multiple_proposals": false
}
```

---

### 3. SCIP (Solving Constraint Integer Programs)

**Type:** Mixed-Integer Programming  
**Best For:** Academic/research use, mixed-integer linear problems

#### When to Use:
- ✅ You have integer variables with linear constraints
- ✅ You want state-of-the-art MIP solving
- ✅ Academic or research environment
- ✅ You need detailed solver statistics

#### Advantages:
- Cutting-edge MIP algorithms
- Excellent solution quality
- Highly configurable
- Good for research and development

#### Considerations:
- May require additional license for commercial use
- Can be slower than CBC for some problems
- More complex configuration options

#### Example Use Cases:
```
- Research projects on procurement optimization
- Benchmarking different formulations
- Problems requiring specific MIP techniques
- Academic case studies
```

---

### 4. CBC (Coin-or Branch and Cut)

**Type:** Mixed-Integer Programming  
**Best For:** Production environments, general MIP problems

#### When to Use:
- ✅ Production deployment
- ✅ Open-source requirement
- ✅ Balanced speed and quality
- ✅ Integer variables with linear constraints

#### Advantages:
- **Open-source** with no licensing concerns
- Good balance of speed and solution quality
- Reliable and battle-tested
- Active community support

#### Example Use Cases:
```
- Production procurement systems
- Enterprise deployments
- Systems requiring open-source solvers
- Mixed-integer procurement problems
```

---

## 🎯 Optimization Strategies

### Strategy 1: LOWEST_COST

**Objective:** Minimize total procurement cost

#### When to Use:
- Budget is the primary concern
- All projects have equal priority
- Cost savings are critical

#### Formula:
```
Minimize: Σ (unit_cost × quantity) for all items
```

#### Best Paired With:
- **GLOP** - for pure cost minimization
- **CP_SAT** - when you have discount rules

---

### Strategy 2: PRIORITY_WEIGHTED

**Objective:** Minimize weighted cost based on project priorities

#### When to Use:
- Projects have different importance levels
- High-priority projects should get preference
- Portfolio-level optimization

#### Formula:
```
Minimize: Σ (unit_cost × quantity × (11 - priority_weight))
```
*High priority (10) gets weight 1, low priority (1) gets weight 10*

#### Best Paired With:
- **CP_SAT** - handles priority weighting naturally
- **CBC** - for production portfolio optimization

---

### Strategy 3: FAST_DELIVERY

**Objective:** Minimize total delivery time

#### When to Use:
- Time to market is critical
- Project deadlines are tight
- Cost is secondary to speed

#### Formula:
```
Minimize: Σ (delivery_time × selection_variable)
```

#### Best Paired With:
- **CP_SAT** - best for time-based optimization
- **SCIP** - when combined with cost constraints

---

### Strategy 4: SMOOTH_CASHFLOW

**Objective:** Distribute spending evenly across time periods

#### When to Use:
- Cash flow stability is important
- Want to avoid spending spikes
- Budget is spread across periods

#### Formula:
```
Minimize: Variance of cash outflows across time periods
```

#### Best Paired With:
- **CP_SAT** - handles variance calculations
- **SCIP** - for complex cash flow rules

---

### Strategy 5: BALANCED

**Objective:** Balance cost, priority, and delivery time

#### When to Use:
- Multi-criteria decision making
- No single factor dominates
- Want well-rounded solutions

#### Formula:
```
Minimize: 0.7 × weighted_cost + 0.3 × delivery_time_factor
```

#### Best Paired With:
- **CP_SAT** - handles multiple objectives well
- **CBC** - for production multi-criteria optimization

---

## 🔬 Graph Algorithms Integration

### Critical Path Analysis

The system now builds a **dependency graph** for your projects and can identify the **critical path** - the longest sequence of dependent items.

#### Use Critical Path To:
1. **Identify bottlenecks** - which items delay the whole project
2. **Prioritize procurement** - focus on critical path items first
3. **Risk management** - monitor high-risk items
4. **Resource allocation** - assign best resources to critical items

#### API Endpoint:
```
GET /finance/optimization-analysis/{run_id}
```

#### Response Example:
```json
{
  "critical_path": ["P1_I001", "P1_I002", "P1_I005"],
  "critical_path_length": 3,
  "network_analysis": {
    "total_nodes": 45,
    "total_edges": 38,
    "connected_components": 3,
    "betweenness_centrality": {...}
  }
}
```

### Network Flow Analysis

Analyzes procurement as a **flow problem** through a network:

- **Nodes:** Project items
- **Edges:** Dependencies and sequences
- **Flow:** Budget and resources

#### Applications:
1. **Bottleneck detection** - find resource constraints
2. **Dependency mapping** - visualize item relationships
3. **Parallel procurement** - identify items that can be procured simultaneously
4. **Centrality analysis** - find most "important" items in the network

---

## 💡 Usage Recommendations

### For Small Projects (< 50 items)

```
✅ Solver: CP_SAT
✅ Strategy: PRIORITY_WEIGHTED or BALANCED
✅ Multiple Proposals: Yes
✅ Time Limit: 60 seconds
```

**Why:** CP-SAT excels at small problems with complex constraints. Multiple proposals help you understand trade-offs.

---

### For Medium Projects (50-500 items)

```
✅ Solver: CP_SAT or CBC
✅ Strategy: Start with all strategies, then focus
✅ Multiple Proposals: Yes for first run, No for subsequent
✅ Time Limit: 300 seconds
```

**Why:** Balance between solution quality and speed. Use proposals to explore options, then commit to one strategy.

---

### For Large Projects (500+ items)

```
✅ Solver: GLOP or CBC
✅ Strategy: LOWEST_COST or PRIORITY_WEIGHTED
✅ Multiple Proposals: No (too expensive)
✅ Time Limit: 600 seconds
```

**Why:** Speed becomes critical. GLOP is fastest for linear problems, CBC for mixed-integer.

---

### For Time-Critical Situations

```
✅ Solver: GLOP
✅ Strategy: FAST_DELIVERY
✅ Multiple Proposals: No
✅ Time Limit: 60 seconds
```

**Why:** GLOP provides fastest solutions. Single strategy reduces computation time.

---

### For Research and Analysis

```
✅ Solver: CP_SAT, GLOP, SCIP, CBC (run all)
✅ Strategy: All strategies
✅ Multiple Proposals: Yes
✅ Time Limit: 600+ seconds
```

**Why:** Compare different solvers and strategies to understand your problem better.

---

## 📈 Performance Comparison

### Typical Execution Times (100 items, 12 time slots)

| Solver | Single Strategy | All Strategies | Solution Quality |
|--------|----------------|----------------|------------------|
| CP_SAT | 15-30s | 60-150s | Excellent |
| GLOP | 2-5s | 10-25s | Good (LP relaxation) |
| SCIP | 20-40s | 80-200s | Excellent |
| CBC | 10-25s | 40-125s | Very Good |

*Note: Times vary based on problem complexity and constraints*

---

## 🛠️ Advanced Features

### 1. Custom Search Heuristics

CP-SAT automatically applies **custom search strategies** based on your chosen optimization strategy:

- **FAST_DELIVERY:** Increased linearization, aggressive preprocessing
- **SMOOTH_CASHFLOW:** Focus on variance reduction
- **PRIORITY_WEIGHTED:** Project priority guides variable ordering

### 2. Multi-Proposal Generation

Generate **multiple solutions** in one run:

```python
# Backend
optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=True,
    strategies=[
        OptimizationStrategy.LOWEST_COST,
        OptimizationStrategy.BALANCED,
        OptimizationStrategy.FAST_DELIVERY
    ]
)
```

Benefits:
- Compare different approaches side-by-side
- Understand cost vs. time trade-offs
- Present multiple options to stakeholders
- Choose best fit for current situation

### 3. Graph-Based Insights

Leverage **NetworkX** graph algorithms:

```python
optimizer._build_dependency_graph()
critical_path = optimizer.get_critical_path()
network_stats = optimizer.analyze_network_flow()
```

Insights:
- **Critical Path:** Longest dependency chain
- **Betweenness Centrality:** Most "important" items
- **Connected Components:** Independent project groups
- **In-Degree Centrality:** Items with most dependencies

---

## 🔄 Migration from Legacy Optimizer

### Step 1: Test with CP_SAT

```python
# Old
optimizer = ProcurementOptimizer(db)
result = await optimizer.run_optimization(request)

# New (backward compatible)
optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
result = await optimizer.run_optimization(request)
```

### Step 2: Experiment with Multiple Proposals

```python
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=True
)
# Review result.proposals
```

### Step 3: Try Different Solvers

```python
# For linear problems
optimizer_glop = EnhancedProcurementOptimizer(db, solver_type=SolverType.GLOP)

# For MIP problems
optimizer_cbc = EnhancedProcurementOptimizer(db, solver_type=SolverType.CBC)
```

### Step 4: Production Deployment

Choose your preferred solver and strategy based on testing:

```python
optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CBC)
result = await optimizer.run_optimization(
    request,
    generate_multiple_proposals=False,
    strategies=[OptimizationStrategy.PRIORITY_WEIGHTED]
)
```

---

## 📚 API Reference

### Enhanced Optimization Endpoint

```http
POST /finance/optimize-enhanced
```

**Query Parameters:**
- `solver_type`: CP_SAT | GLOP | SCIP | CBC
- `generate_multiple_proposals`: boolean
- `strategies`: Array of strategy types (optional)

**Request Body:**
```json
{
  "max_time_slots": 12,
  "time_limit_seconds": 300
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "OPTIMAL",
  "execution_time_seconds": 45.2,
  "total_cost": 1250000.00,
  "items_optimized": 120,
  "proposals": [
    {
      "proposal_name": "Priority-Weighted Strategy",
      "strategy_type": "PRIORITY_WEIGHTED",
      "total_cost": 1250000.00,
      "weighted_cost": 8750000.00,
      "status": "OPTIMAL",
      "items_count": 120,
      "decisions": [...],
      "summary_notes": "CP-SAT solver: 120 items optimized"
    }
  ]
}
```

### Solver Information

```http
GET /finance/solver-info
```

Returns detailed information about all available solvers and strategies.

### Optimization Analysis

```http
GET /finance/optimization-analysis/{run_id}
```

Returns graph-based analysis including critical path and network statistics.

---

## 🎓 Best Practices

### 1. Start Simple, Then Optimize

```
1. First run: CP_SAT with all strategies → understand your problem
2. Second run: Choose best strategy, single proposal → refine
3. Production: Selected solver + strategy → fast execution
```

### 2. Use Time Limits Wisely

- **Development:** 60-120 seconds for quick iterations
- **Analysis:** 300-600 seconds for thorough exploration
- **Production:** 120-300 seconds for balanced speed/quality

### 3. Monitor Solution Quality

```python
if proposal.status == "OPTIMAL":
    # Use this solution
elif proposal.status == "FEASIBLE":
    # Consider increasing time_limit_seconds
else:
    # Problem may be infeasible - check constraints
```

### 4. Leverage Multiple Proposals

Use different strategies for different stakeholders:
- **CFO:** LOWEST_COST proposal
- **Operations:** FAST_DELIVERY proposal
- **Management:** BALANCED proposal

### 5. Understand Your Problem Type

**Linear Problem?** → Use GLOP  
**Complex Constraints?** → Use CP_SAT  
**Production MIP?** → Use CBC  
**Research?** → Use SCIP or compare all

---

## 🐛 Troubleshooting

### Problem: Solver Returns INFEASIBLE

**Solutions:**
1. Check budget constraints - may be too tight
2. Verify all items have valid delivery options
3. Review locked decisions - they may conflict
4. Try different time_limit_seconds
5. Use GLOP for quick feasibility check

### Problem: Solutions Take Too Long

**Solutions:**
1. Reduce `time_limit_seconds`
2. Switch to GLOP for faster solutions
3. Disable `generate_multiple_proposals`
4. Reduce `max_time_slots`

### Problem: GLOP Solutions Not Optimal

**Explanation:** GLOP uses LP relaxation with rounding

**Solutions:**
1. Use CP_SAT or CBC for true integer optimization
2. Accept small optimality gap for speed
3. Use GLOP for initial feasibility, then refine with CBC

### Problem: Different Solvers Give Different Results

**Explanation:** This is normal!

- GLOP rounds LP relaxation → approximate
- CP_SAT, SCIP, CBC all find true optimal → may differ due to tie-breaking
- Different strategies → different objectives

---

## 📞 Support and Resources

### OR-Tools Documentation
- Official Docs: https://developers.google.com/optimization
- CP-SAT Guide: https://developers.google.com/optimization/cp/cp_solver
- Linear Solver: https://developers.google.com/optimization/lp/lp

### System-Specific Help
- Check `/finance/solver-info` endpoint for solver capabilities
- Review optimization logs in backend
- Use network analysis for dependency insights

---

## 🚀 Future Enhancements

Potential areas for further optimization:

1. **Column Generation** - for very large problems
2. **Decomposition Methods** - for multi-stage problems
3. **Metaheuristics** - for extremely large instances
4. **Machine Learning** - to predict good starting solutions
5. **Real-time Optimization** - dynamic re-optimization
6. **Stochastic Programming** - handle uncertainty
7. **Multi-objective Pareto** - explicit Pareto frontier generation

---

## 📝 Summary

Your enhanced procurement system now provides:

✅ **4 Solvers:** CP_SAT, GLOP, SCIP, CBC  
✅ **5 Strategies:** Cost, Priority, Speed, Cash Flow, Balanced  
✅ **Graph Analysis:** Critical path, network flow  
✅ **Multi-Proposal:** Compare strategies side-by-side  
✅ **Production-Ready:** Battle-tested algorithms  

**Choose wisely, optimize efficiently!** 🎯

