## Build the documentation locally

```bash
cd docs # From project's root
make clean
rm -rf source/generated # remove autodoc artefacts, that are not removed by `make clean`
make html
```
