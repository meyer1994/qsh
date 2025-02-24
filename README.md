# qsh (Quick SHell)

A simple and easy to use AI for your shell

## Usage

```bash
echo 'hello world' | curl -F u=@- 'https://qsh.jmeyer.dev' > main.py
cat main.py
# print('Hello, World!')
```

You can also add a system prompt to the request:

```bash
echo 'always use double quotes' > system.txt
echo 'hello world' | curl -F u=@- -F s=@system.txt 'https://qsh.jmeyer.dev' > main.py
cat main.py
# print("Hello, World!")
```

### Alias

```bash
alias qsh='curl -F u=@- -F s=@system.txt "https://qsh.jmeyer.dev"'
echo 'hello world' | qsh
# print("Hello, World!")
```

## How It Works

When you pipe a Python code snippet into the endpoint, the service processes the
input and returns a complete Python program. For example:

```bash
echo 'a small python program' | curl -F u=@- "https://qsh.jmeyer.dev"
# the resulting program is written to stdout by curl
```

Requests are cached for 1 day.

## Development

We use `uv` for development.

```bash
uv sync
```

### Testing

```bash
uv run python -m unittest -vb test_handler.py
```

### Deploying

```bash
make deploy
make destroy  # to clean up
```
