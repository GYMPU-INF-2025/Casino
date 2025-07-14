# Casino

To run this you need to first have [uv installed](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2).

After that run:
```cmd
uv venv
```

In the root directory of the project.

To install all the dependency run:
```cmd
uv sync
```


To start the Backend process run 
```cmd
uv run sanic backend.main.app --debug
```
In the root directory of the project. You can remove the `--debug` flag to disable debug loggin.

To run the Frontend process run
```cmd
uv run -m frontend
```
