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

GitHub Actions will test, build, and publish the distribution to PyPI after the `pypi` environment approval.

## Version updates

Before the next release, update the version in `pyproject.toml` and tag the same version:

```text
pyproject.toml version = "0.1.1"
git tag -a v0.1.1 -m "Release v0.1.1"
```
