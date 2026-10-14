# Release to PyPI

`main` is the only branch. Releases are published from it by pushing a version tag.

## One-time PyPI setup

1. Create or sign in to your PyPI account.
2. Open PyPI's trusted publisher setup.
3. Add a publisher with:
   - PyPI project name: `eisfit`
   - Owner: `shiyunliu-battery`
   - Repository: `Battery-EIS-Fit`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
4. In GitHub repository settings, create an environment named `pypi`.
5. For safety, require manual approval on the `pypi` environment.

## Release checklist

1. On `main`, update `version` in `pyproject.toml` and the version badge in `README.md`.
2. Add a `## <version>` section at the top of `CHANGELOG.md`. The release fails
   before publication if this section is missing, and the GitHub release notes are
   taken from it.
3. Check locally:

   ```bash
   pytest
   ruff check src tests
   python -m build
   twine check dist/*
   ```

4. Commit, push `main`, wait for CI to pass, then tag the same commit and push the tag:

   ```bash
   git push origin main
   git tag -a v0.2.0 -m "eisfit 0.2.0"
   git push origin v0.2.0
   ```

The tag must equal `v` plus the version in `pyproject.toml`. GitHub Actions then
tests, builds and publishes to PyPI after any configured `pypi` environment
approval, and creates the GitHub release for the tag.
