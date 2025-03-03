# New workflow with uv

1. Run tests
```
$ uv run -m pytest
```

# Old workflow

Do below in the main environment (e.g., labenv3.10)

1. Typing check by 
```
$ mypy src
```

2. Bump version
``src/hicsv/__init__.py``
``pyproject.toml``
``_docs/conf.py``

2. Build docs by
```
$ cd _docs
$ make html
```

3. Commit and push

4. Package by
```
$ python -m build --sdist
$ python -m build --wheel
$ twine check dist/*
```

5. Upload to PyPI
```
$ twine upload --repository pypi dist/*
```

6. Generate recipe by grayskull (optional)
In another envrionment with grayskull (e.g., env_grayskull)
```
$ grayskull pypi --strict-conda-forge hicsv-python
```
Modify hicsv-python/meta.yaml if necessary. e.g. web page & maintainer ID

## Updating

See https://conda-forge.org/docs/maintainer/updating_pkgs.html

1. Do 1-5 above

2. Go to https://github.com/conda-forge/hicsv-python-feedstock

3. Fork the repo

4. Create branch (e.g., update_1_0_1)

4. In that branch, make change to recipe/meta.yaml
Version number and SHA256 (get it from PYPI web page)

5. Commit the change

6. Open pull request in that branch

Include @conda-forge-admin, please rerender
in the comment. 
