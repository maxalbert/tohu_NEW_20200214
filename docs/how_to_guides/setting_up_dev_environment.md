# Setting up a development environment

`tohu` uses [poetry](https://python-poetry.org/) for dependency management, so make sure you have it [installed](https://python-poetry.org/docs/#installation).

Next, install the necessary dependencies for `tohu`.
We specify the `--extras` options to install the complete set of packages for a full development environment.
```
$ poetry install --extras "develop testing docs deploy"
```
