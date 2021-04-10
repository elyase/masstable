# masstable

<p align="center">
    <em>Utilities for working with nuclear mass tables</em>
</p>

[![build](https://github.com/elyase/masstable/workflows/Build/badge.svg)](https://github.com/elyase/masstable/actions)
[![codecov](https://codecov.io/gh/elyase/masstable/branch/master/graph/badge.svg)](https://codecov.io/gh/elyase/masstable)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=elyase/masstable)](https://dependabot.com)
[![PyPI version](https://badge.fury.io/py/masstable.svg)](https://badge.fury.io/py/masstable)

---

**Documentation**: <a href="https://elyase.github.io/masstable/" target="_blank">https://elyase.github.io/masstable/</a>

**Source Code**: <a href="https://github.com/elyase/masstable" target="_blank">https://github.com/elyase/masstable</a>

---

## Development

### Setup environement

You should have [Pipenv](https://pipenv.readthedocs.io/en/latest/) installed. Then, you can install the dependencies with:

```bash
pipenv install --dev
```

After that, activate the virtual environment:

```bash
pipenv shell
```

### Run unit tests

You can run all the tests with:

```bash
make test
```

Alternatively, you can run `pytest` yourself:

```bash
pytest
```

### Format the code

Execute the following command to apply `isort` and `black` formatting:

```bash
make format
```

## License

This project is licensed under the terms of the MIT license.
