# Known Limitations (RC1)

1. Frontend build completes with existing eslint warnings in legacy/untouched areas.
2. Backend tests pass but include existing deprecation warnings.
3. Historical scripts/docs outside hardened update paths may still have older examples; use packaged scripts in this release.
4. This package is prepared for controlled rollout; broader warning cleanup and non-critical UX polish are outside RC1 scope.
5. Current backend container build context requires `backend/VERSION` to be kept aligned with root `VERSION` for runtime `/health` version visibility.
