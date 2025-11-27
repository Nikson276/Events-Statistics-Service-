# Repository Guidelines

This document provides essential guidelines for contributors to ensure consistency,
quality, and smooth collaboration in the **tunec** project.

## Project Structure & Module Organization
- `src/`: application source code and modules
- `tests/`: unit and integration tests
- `assets/`: static files (images, stylesheets)
- `docs/`: additional documentation and design notes
- `config/`: example and template configuration files

## Build, Test, and Development Commands
- `make build`: compile assets and bundle source code
- `make dev`: launch development server with live reload
- `make test`: run all tests and generate coverage report
- `make lint`: execute linters (ESLint, Flake8) and formatters (Prettier)

## Coding Style & Naming Conventions
- Indentation: 2 spaces for JavaScript/TypeScript, 4 spaces for Python
- Filenames: kebab-case (e.g., `user-service.ts`)
- Identifiers: camelCase for variables/functions, PascalCase for classes
- Use Prettier for formatting and ESLint/Flake8 for linting

## Testing Guidelines
- Frameworks: Jest (`*.spec.ts`) for JS/TS, PyTest (`*_test.py`) for Python
- Test location: mirror source path under `tests/` directory
- Coverage: maintain ≥80%—view HTML report in `coverage/`
- Run: `make test` or `npm test`/`pytest`

## Commit & Pull Request Guidelines
- Commit messages: follow [Conventional Commits](https://www.conventionalcommits.org)
  - format: `type(scope): short description`
  - example: `feat(cli): add deploy command`
- Pull request:
  - link related issue (e.g., `#45`)
  - include clear description and screenshots if applicable
  - assign at least two reviewers before merging

## Security & Configuration Tips
- Store secrets in `.env`; commit only `.env.example`
- Regularly run `npm audit` or `pip-audit` to surface vulnerabilities

## Architecture Overview
- Core logic in `src/core/`
- API endpoints in `src/api/`
- CLI commands in `src/cli/`

> **Keep this guide updated** as the project evolves to help all contributors.
