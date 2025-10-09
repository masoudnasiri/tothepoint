# OR-Tools Optimization Quick Reference Card

## 🚀 Quick Solver Selection

| Your Situation | Recommended Solver | Strategy |
|---------------|-------------------|----------|
| First time using system | **CP_SAT** | All strategies |
| Small project (< 50 items) | **CP_SAT** | PRIORITY_WEIGHTED |
| Medium project (50-500 items) | **CP_SAT** or **CBC** | BALANCED |
| Large project (500+ items) | **GLOP** or **CBC** | LOWEST_COST |
| Need results fast | **GLOP** | Any |
| Complex discounts/rules | **CP_SAT** | Any |
| Production deployment | **CBC** | PRIORITY_WEIGHTED |
| Budget is critical | **GLOP** | LOWEST_COST |
| Time is critical | **CP_SAT** | FAST_DELIVERY |
| Research/testing | **All solvers** | All strategies |

---

## 🎯 Solver Comparison at a Glance

| Feature | CP_SAT | GLOP | SCIP | CBC |
|---------|--------|------|------|-----|
| **Type** | Constraint Programming | Linear Programming | Mixed-Integer | Mixed-Integer |
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Complexity** | High | Low | High | Medium |
| **Scale** | Medium | Very Large | Medium | Large |
| **License** | Apache 2.0 | Apache 2.0 | Academic/ZIB | EPL (Open) |
| **Best For** | Complex constraints | Pure LP | Research | Production |

---

## 📊 Strategy Cheat Sheet

### LOWEST_COST
```
🎯 Goal: Minimize total spending
💰 Cost focused: 100%
⏱️ Time focused: 0%
🏆 Priority focused: 0%
```
**Use when:** Budget is the only concern

### PRIORITY_WEIGHTED
```
🎯 Goal: Optimize by project importance
💰 Cost focused: Weighted by priority
⏱️ Time focused: 0%
🏆 Priority focused: 100%
```
**Use when:** Different projects have different importance

### FAST_DELIVERY
```
🎯 Goal: Get items as soon as possible
💰 Cost focused: 0%
⏱️ Time focused: 100%
🏆 Priority focused: 0%
```
**Use when:** Deadlines are tight

### SMOOTH_CASHFLOW
```
🎯 Goal: Even distribution of spending
💰 Cost focused: Variance minimization
⏱️ Time focused: Spread across periods
🏆 Priority focused: 0%
```
**Use when:** Cash flow stability matters

### BALANCED
```
🎯 Goal: Multi-criteria optimization
💰 Cost focused: 50%
⏱️ Time focused: 30%
🏆 Priority focused: 20%
```
**Use when:** No single factor dominates

---

## ⚡ Performance Quick Guide

### Typical Execution Times

**Small (< 50 items):**
- CP_SAT: 5-15 seconds
- GLOP: 1-3 seconds
- CBC: 3-8 seconds

**Medium (50-500 items):**
- CP_SAT: 30-120 seconds
- GLOP: 5-15 seconds
- CBC: 15-60 seconds

**Large (500+ items):**
- CP_SAT: May timeout
- GLOP: 20-60 seconds ✅
- CBC: 60-300 seconds ✅

---

## 🔧 Configuration Templates

### For Quick Results
```json
{
  "solver_type": "GLOP",
  "max_time_slots": 12,
  "time_limit_seconds": 60,
  "generate_multiple_proposals": false,
  "strategies": ["LOWEST_COST"]
}
```

### For Best Quality
```json
{
  "solver_type": "CP_SAT",
  "max_time_slots": 12,
  "time_limit_seconds": 300,
  "generate_multiple_proposals": true,
  "strategies": []  // all strategies
}
```

### For Production
```json
{
  "solver_type": "CBC",
  "max_time_slots": 12,
  "time_limit_seconds": 180,
  "generate_multiple_proposals": false,
  "strategies": ["PRIORITY_WEIGHTED"]
}
```

### For Analysis/Research
```json
{
  "solver_type": "CP_SAT",
  "max_time_slots": 24,
  "time_limit_seconds": 600,
  "generate_multiple_proposals": true,
  "strategies": []  // all strategies
}
```

---

## 🎨 Frontend Usage

### 1. Access Enhanced Optimization
```
Navigate to: /optimization-enhanced
```

### 2. Select Solver
Click on solver card or use dropdown:
- **CP_SAT** - For complex constraints
- **GLOP** - For speed
- **SCIP** - For research
- **CBC** - For production

### 3. Configure & Run
1. Set time slots (default: 12)
2. Set time limit (default: 300s)
3. Enable/disable multiple proposals
4. Select strategies (optional)
5. Click "Run Optimization"

### 4. Review Results
- Switch between proposal tabs
- Compare costs and strategies
- Review decision details
- Save preferred proposal

---

## 🔍 Graph Analysis Features

### Critical Path
```
Endpoint: GET /finance/optimization-analysis/{run_id}

Returns:
- Critical path items
- Network statistics
- Dependency insights
```

**Use to identify:**
- Bottleneck items
- High-priority procurement
- Project delays
- Risk areas

### Network Flow
```
Analysis includes:
- Total nodes (items)
- Total edges (dependencies)
- Connected components
- Centrality measures
```

**Use to optimize:**
- Parallel procurement
- Resource allocation
- Dependency management
- Risk mitigation

---

## 📱 API Endpoints Quick Reference

### Run Enhanced Optimization
```http
POST /finance/optimize-enhanced?solver_type=CP_SAT&generate_multiple_proposals=true
Body: { "max_time_slots": 12, "time_limit_seconds": 300 }
```

### Get Solver Info
```http
GET /finance/solver-info
Returns: Available solvers and strategies
```

### Get Optimization Analysis
```http
GET /finance/optimization-analysis/{run_id}
Returns: Graph analysis and critical path
```

### Legacy Optimization (Backward Compatible)
```http
POST /finance/optimize
Body: { "max_time_slots": 12, "time_limit_seconds": 300 }
```

---

## ⚠️ Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| **INFEASIBLE result** | 1. Check budget constraints<br>2. Verify delivery options<br>3. Review locked items<br>4. Increase time slots |
| **Too slow** | 1. Switch to GLOP<br>2. Disable multiple proposals<br>3. Reduce time limit<br>4. Reduce max_time_slots |
| **Results vary** | Normal! Different solvers/strategies = different objectives |
| **GLOP not optimal** | Expected - uses LP relaxation. Use CP_SAT/CBC for true optimal |
| **Timeout errors** | 1. Increase time_limit_seconds<br>2. Use faster solver (GLOP)<br>3. Reduce problem size |

---

## 🎓 Learning Path

### Week 1: Basics
1. Run CP_SAT with PRIORITY_WEIGHTED
2. Review single proposal
3. Save decisions
4. Lock approved items

### Week 2: Exploration
1. Enable multiple proposals
2. Compare different strategies
3. Understand trade-offs
4. Test different solvers

### Week 3: Optimization
1. Find best solver for your data
2. Choose preferred strategy
3. Tune time limits
4. Establish production workflow

### Week 4: Advanced
1. Use graph analysis
2. Identify critical paths
3. Leverage network insights
4. Optimize large projects

---

## 💡 Pro Tips

1. **Always start with multiple proposals** - understand your options
2. **Use CP_SAT for development** - most flexible
3. **Switch to GLOP/CBC for production** - faster and reliable
4. **Monitor execution time** - tune time_limit_seconds accordingly
5. **Check critical path** - focus on bottleneck items
6. **Lock decisions progressively** - not all at once
7. **Compare proposals visually** - use the tabs interface
8. **Save solver config** - reuse successful configurations
9. **Test with smaller time_slots first** - faster iterations
10. **Review network analysis** - optimize dependencies

---

## 📚 Resources

- **Full Guide:** `OR_TOOLS_ENHANCEMENT_GUIDE.md`
- **API Docs:** `/docs` endpoint (FastAPI Swagger UI)
- **Solver Info:** `/finance/solver-info` endpoint
- **OR-Tools Docs:** https://developers.google.com/optimization

---

## 🎯 Decision Tree

```
Start
  │
  ├─ Problem Size?
  │   ├─ Small (< 50 items) ──> CP_SAT
  │   ├─ Medium (50-500) ────> CP_SAT or CBC
  │   └─ Large (500+) ────────> GLOP or CBC
  │
  ├─ Main Concern?
  │   ├─ Cost ──────────────> LOWEST_COST strategy
  │   ├─ Time ──────────────> FAST_DELIVERY strategy
  │   ├─ Priority ──────────> PRIORITY_WEIGHTED strategy
  │   ├─ Cash Flow ────────> SMOOTH_CASHFLOW strategy
  │   └─ Balance ───────────> BALANCED strategy
  │
  ├─ First Time?
  │   └─ Yes ──> CP_SAT + All Strategies + Multiple Proposals
  │
  ├─ Production?
  │   └─ Yes ──> CBC + Selected Strategy + Single Proposal
  │
  └─ Research?
      └─ Yes ──> All Solvers + All Strategies + Analysis
```

---

## ✅ Pre-Flight Checklist

Before running optimization:

- [ ] All active projects have items
- [ ] All items have delivery options
- [ ] Budget data is loaded for required periods
- [ ] Procurement options exist for all item codes
- [ ] Locked decisions are intentional
- [ ] Solver type is appropriate for problem size
- [ ] Time limit is reasonable (60-600 seconds)
- [ ] Strategy matches business objectives

---

**Happy Optimizing! 🚀**

*For detailed explanations, see `OR_TOOLS_ENHANCEMENT_GUIDE.md`*

