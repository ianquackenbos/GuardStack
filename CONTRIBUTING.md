# Contributing to GuardStack

First off, thank you for considering contributing to GuardStack! It's people like you that make GuardStack such a great tool for the AI safety community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@guardstack.io](mailto:conduct@guardstack.io).

## Getting Started

### Types of Contributions

There are many ways to contribute to GuardStack:

- 🐛 **Bug Reports**: Found a bug? Let us know!
- 💡 **Feature Requests**: Have an idea? We'd love to hear it!
- 📝 **Documentation**: Help improve our docs
- 🔧 **Code**: Submit bug fixes or new features
- 🧪 **Testing**: Help us improve test coverage
- 🌍 **Translations**: Help translate the UI

### First Time Contributors

Look for issues labeled `good first issue` - these are specifically curated for new contributors:

```
https://github.com/guardstack/guardstack/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22
```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/guardstack.git
cd guardstack

# Add upstream remote
git remote add upstream https://github.com/guardstack/guardstack.git
```

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies with dev extras
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Start infrastructure
docker-compose up -d postgres redis minio

# Run migrations
alembic upgrade head

# Start the API server
uvicorn guardstack.main:app --reload
```

### Frontend Setup

```bash
cd pkg/guardstack

# Install dependencies
npm install

# Start development server
npm run dev
```

### Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check src/
mypy src/

# Frontend linting
cd pkg/guardstack
npm run lint
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-new-connector` - New features
- `fix/evaluation-timeout` - Bug fixes
- `docs/api-reference` - Documentation
- `refactor/scoring-module` - Code refactoring
- `test/genai-pillars` - Test additions

### Creating a Branch

```bash
# Update your local main
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/your-feature-name
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `build`: Build system or dependencies
- `ci`: CI configuration
- `chore`: Other changes (e.g., updating .gitignore)

#### Examples

```bash
feat(connectors): add Azure OpenAI connector

fix(evaluation): handle timeout in Garak runner

docs(readme): add Kubernetes installation guide

test(predictive): add fairness pillar unit tests
```

## Pull Request Process

### Before Submitting

1. **Update your branch**: Rebase on the latest main
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**: Ensure all tests pass
   ```bash
   pytest
   ```

3. **Run linters**: Fix any issues
   ```bash
   ruff check src/ --fix
   mypy src/
   ```

4. **Update documentation**: If you changed APIs or added features

### PR Template

When creating a PR, please include:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe tests that you ran

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
```

### Review Process

1. A maintainer will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

## Style Guidelines

### Python

We use:
- **ruff** for linting
- **black** for formatting (via ruff)
- **mypy** for type checking

```bash
# Format code
ruff format src/

# Lint and fix
ruff check src/ --fix

# Type check
mypy src/
```

#### Python Guidelines

```python
# Use type hints
def calculate_score(results: list[float], weights: dict[str, float]) -> float:
    ...

# Use docstrings (Google style)
def evaluate_model(model_id: str) -> EvaluationResult:
    """
    Evaluate a registered model.
    
    Args:
        model_id: The unique identifier of the model.
        
    Returns:
        The evaluation result with pillar scores.
        
    Raises:
        ModelNotFoundError: If the model doesn't exist.
    """
    ...

# Use async/await for I/O operations
async def fetch_model(model_id: str) -> Model:
    async with get_session() as session:
        return await session.get(Model, model_id)
```

### TypeScript/Vue

We use:
- **ESLint** for linting
- **Prettier** for formatting

```bash
cd pkg/guardstack
npm run lint
npm run format
```

#### Vue Guidelines

```vue
<script setup lang="ts">
// Use Composition API with script setup
import { ref, computed, onMounted } from 'vue';
import type { Model } from '../types';

// Props with type definitions
const props = defineProps<{
  modelId: string;
  showDetails?: boolean;
}>();

// Emits with type definitions
const emit = defineEmits<{
  (e: 'update', value: Model): void;
  (e: 'delete', id: string): void;
}>();

// Reactive state
const model = ref<Model | null>(null);
const isLoading = ref(false);

// Computed properties
const displayName = computed(() => model.value?.name ?? 'Unknown');
</script>
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=guardstack --cov-report=html

# Run specific module
pytest tests/test_predictive.py

# Run specific test
pytest tests/test_predictive.py::test_fairness_evaluation

# Run with verbose output
pytest -v

# Run integration tests
pytest tests/integration/ --integration
```

### Writing Tests

```python
import pytest
from guardstack.predictive.pillars import FairnessPillar

@pytest.fixture
def fairness_pillar():
    return FairnessPillar()

@pytest.mark.asyncio
async def test_fairness_evaluation(fairness_pillar):
    """Test fairness pillar evaluation."""
    result = await fairness_pillar.evaluate(
        model=mock_model,
        dataset=mock_dataset,
    )
    
    assert result.score >= 0.0
    assert result.score <= 1.0
    assert 'demographic_parity' in result.metrics

@pytest.mark.parametrize("threshold,expected", [
    (0.8, "pass"),
    (0.5, "warn"),
    (0.3, "fail"),
])
def test_score_classification(threshold, expected):
    """Test score to status classification."""
    status = classify_score(threshold)
    assert status == expected
```

### Frontend Tests

```bash
cd pkg/guardstack

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

## Documentation

### Docstrings

All public functions, classes, and modules should have docstrings:

```python
class ModelEvaluator:
    """
    Evaluates AI models against safety and security pillars.
    
    This class orchestrates the evaluation process, running each
    pillar's assessment and aggregating the results.
    
    Attributes:
        pillars: List of pillar evaluators to run.
        scorer: Score aggregation service.
        
    Example:
        ```python
        evaluator = ModelEvaluator(pillars=[fairness, robustness])
        result = await evaluator.evaluate(model)
        print(f"Score: {result.overall_score}")
        ```
    """
```

### API Documentation

API changes should include:
- Updated OpenAPI descriptions
- Example requests/responses
- Error codes and descriptions

### User Documentation

For user-facing features:
- Update relevant docs in `docs/`
- Add screenshots if UI changes
- Include examples

## Community

### Getting Help

- **Discord**: [Join our community](https://discord.gg/guardstack)
- **Discussions**: [GitHub Discussions](https://github.com/guardstack/guardstack/discussions)
- **Stack Overflow**: Tag questions with `guardstack`

### Maintainers

- Review PRs within 48 hours
- Provide constructive feedback
- Help new contributors

---

## Thank You!

Your contributions make GuardStack better for everyone in the AI safety community. We appreciate your time and effort!

<p align="center">
  <strong>Happy Contributing! 🎉</strong>
</p>
