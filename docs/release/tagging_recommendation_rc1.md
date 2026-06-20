# Tagging Recommendation - RC1

## Recommendation

- Suggested tag: `v1.0.0-rc1`
- Suggested release title: `Corbit Rivar v1.0.0-rc1`
- Release posture: `Pilot Release Candidate`

## Tag Target Recommendation

Use one of:

1. `94a8a86` (accepted Phase 11A branding identity commit), or
2. Latest Phase 11B release-control commit (preferred if including pilot deployment verification + package refresh artifacts in tagged snapshot).

## Current Policy

- Do **not** create or push tag automatically in this phase.
- Create tag only after explicit approval following pilot governance review.

## Suggested Commands (when approved)

```bash
git checkout restart/baseline-before-github-push
git pull
git tag -a v1.0.0-rc1 <target-commit> -m "Corbit Rivar v1.0.0-rc1"
git push origin v1.0.0-rc1
```
