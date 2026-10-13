# Release to PyPI

This repository publishes the clean package from the `public` branch.

## One-time PyPI setup

1. Create or sign in to your PyPI account.
2. Open PyPI's trusted publisher setup.
3. Add a pending publisher with:
   - PyPI project name: `eisfit`
   - Owner: `shiyunliu-battery`
   - Repository: `Battery-EIS-Fit`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
4. In GitHub repository settings, create an environment named `pypi`.
5. For safety, require manual approval on the `pypi` environment.

## Release checklist

Run locally from the `public` branch:

```bash
pytest
python -m compileall src tests
python -m build
twine check dist/*
```

Then tag and push:

```bash
git switch public
git pull --ff-only origin public
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

GitHub Actions will test, build, and publish the distribution to PyPI after any
configured `pypi` environment approval.

## Release branch

The same publishing workflow also accepts a `release/<version>` branch. The
branch suffix must match the package version in `pyproject.toml`; a mismatch
fails before publication. Prepare the version update and changelog from
`public`, then push the release branch:

```bash
git switch -c release/0.1.1 public
git push origin release/0.1.1
```

After successful PyPI publication, the workflow creates the matching GitHub
tag and release at the exact published commit. Merge the release changes back
into `public`. The tag workflow is still available for subsequent releases.

## Version updates

Before the next release, update the version in `pyproject.toml` and tag the same version:

```text
pyproject.toml version = "0.1.1"
git tag -a v0.1.1 -m "Release v0.1.1"
```
