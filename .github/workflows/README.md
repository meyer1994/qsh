# QSH

QSH (Query Shell) is a serverless FastAPI application deployed on AWS Lambda that
provides a natural language interface for shell commands. It uses OpenAI's API to
interpret user queries and convert them into executable shell commands, making
command-line operations more accessible to users who are less familiar with terminal
syntax.

## Requirements:

- Python 3.12
- Poetry
- AWS SAM CLI
- AWS credentials configured

## Development Setup:

Install poetry:

```bash
pipx install poetry
```

Install dependencies:

```bash
poetry install
```

Set up environment variables:

```bash
OPENAI_API_KEY=your_key_here
```

## Development Commands:

- Run linter: `poetry run ruff check .`
- Run type checker: `poetry run mypy .`
- Build project: `make build`
- Clean build artifacts: `make clean`

## Deployment:

Build the project:

```bash
make build
```

Deploy to AWS (guided):

```bash
make deploy
```

(Follow the prompts to configure deployment settings)

## CI/CD:

The project uses GitHub Actions for continuous integration and deployment:

- Build workflow runs on all pushes and pull requests to main
- Deploy workflow runs only on pushes to main
- Required secrets for deployment:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY

## Project Structure:

- `/src` - Application source code
- `/scripts` - Build and deployment scripts
- `/dependencies` - Lambda layer dependencies
- `template.yaml` - SAM template for AWS resources
- `pyproject.toml` - Poetry and tool configurations
- `.github/workflows` - CI/CD configurations

Note: The `poetry.lock` file is gitignored. After cloning, run `poetry install` to
generate it locally.

For local development with SAM CLI:

```bash
sam local start-api
```

For more detailed configuration references, see:

- SAM template configuration: `template.yaml`
- Python dependencies and tools: `pyproject.toml`
- Build process: `Makefile`
- CI/CD workflows: `.github/workflows/build.yml` and `.github/workflows/deploy.yml`
