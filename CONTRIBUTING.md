# 🤝 Contributing to ALIVE

Thank you for your interest in contributing to **ALIVE** (Avatar Liveness for Intelligent Virtual Empathy)!  
Whether you're fixing bugs, adding features, improving docs, or suggesting ideas — your help is welcome and appreciated.

---

## 🧱 Repository Structure

```txt
/
├── eva/                  # Python FastAPI backend (WebSocket + RAG + LLM)
├── avatar/               # ASP.NET Core frontend/backend (avatar, speech, UI)
├── docs/ (planned)       # Documentation pages
├── .env.example          # Environment variables template
├── compose.example.yaml  # Docker Compose definition
├── Eva.Containerfile     # Dockerfile for eva service
├── Avatar.Containerfile  # Dockerfile for avatar service
```

---

## 🛠 Development Setup

### Prerequisites

- Python 3.11+ with `pip`
- .NET 6.0+ SDK
- Docker & Docker Compose (or Podman)

### Quick Start with Docker (Recommended)

```bash
cp .env.example .env
cp compose.example.yaml compose.yaml
# make sure the external network is created
docker network create sermas-external 2>/dev/null || true
# (on windows, that would be sth like):
# assuming PowerShell is used
# if (-not (docker network inspect sermas-external -ErrorAction SilentlyContinue)) {
#     docker network create sermas-external
# }
docker compose --env-file .env up --build
```

Services run at:

- EVA WebSocket: `ws://localhost:8000/ws`
- Avatar UI/API: `http://localhost:8080`

---

## ▶️ Running Without Docker

### EVA (Python)

```bash
cd eva
python -m venv venv
source venv/bin/activate
pip install -r requirements/all.txt
python -m eva.main
```

### AVATAR (C#)

```bash
# Linux/macOS - Activate environment variables
set -a
. ./.env
set +a

cd avatar
dotnet restore
dotnet run
```

```powershell
# Windows PowerShell - Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim('"').Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

cd avatar
dotnet restore
dotnet run
```

> Ensure your `.env` values (e.g., `CHAT_API_KEY`, `DID_API_KEY`) are set in the environment or `appsettings.json`.

---

## 🧪 Running Tests

### Run Tests for EVA (Python)

```bash
cd eva
pytest
```

### Run Tests for Avatar (C#)

```bash
cd avatar
dotnet test
```

> Test coverage reports are generated using `pytest-cov` for Python components.

---

## 🧼 Code Style & Linting

We use the following tools to maintain code quality:

- **Python**: `ruff`, `black`, `isort`, `mypy`
- **C#**: .NET analyzers + formatting via `dotnet format`

### Run Formatters

```bash
# Python (using hatch)
hatch run lint

# Python (manual commands)
black --config pyproject.toml --check --diff eva tests scripts
mypy --config pyproject.toml eva tests scripts
ruff check --config pyproject.toml eva tests scripts
pylint --rcfile=pyproject.toml eva tests scripts

# C#
dotnet format AliveOnD-ID.csproj
```

---

## 🐛 Reporting Issues

Before creating an issue:

- **Check existing issues** to avoid duplicates
- **Use issue templates** (if available)
- **Include reproduction steps** with expected vs actual behavior
- **Provide environment details** (OS, Python/Node versions, Docker version, etc.)
- **Include relevant logs** or error messages

For bug reports, please include:

- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment information
- Relevant configuration (with sensitive data removed)

---

## 📝 How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/your-change`)
3. **Make your changes** following our coding standards
4. **Add tests** for new features or bug fixes
5. **Update documentation** as needed
6. **Commit your changes** with clear, concise messages
7. **Push to your fork** (`git push origin feature/your-change`)
8. **Open a pull request** with a detailed description

---

## 📋 Pull Request Guidelines

When submitting a pull request:

- **Link to related issues** using keywords like "Fixes #123"
- **Include tests** for new features or bug fixes
- **Update documentation** as needed (README, code comments, etc.)
- **Ensure CI passes** (all tests, linting, formatting)
- **Keep changes focused** - one feature/fix per PR
- **Write clear commit messages** following conventional commits format
- **Add a detailed PR description** explaining what changed and why

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)
- [ ] Linked to relevant issues

---

## 💡 Contribution Ideas

Here are some areas where we'd love your help:

- **Core Features**: Improve emotion detection or TTS mapping
- **User Experience**: Enhance WebRTC UX or avatar responsiveness
- **Infrastructure**: Add new authentication or deployment options
- **Documentation**: Expand usage examples and API documentation
- **Testing**: Improve test coverage and add integration tests
- **Performance**: Optimize response times and resource usage
- **Accessibility**: Make the interface more accessible
- **Internationalization**: Add support for additional languages

---

## 🆘 Getting Help

If you need help or have questions:

- **GitHub Discussions**: For general questions and community support
- **Issues**: For bug reports and feature requests
- **Documentation**: Check the docs folder and README files
- **Code Comments**: Most functions and classes are documented inline

---

## 🛡️ Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).  
Be respectful and inclusive — harassment or discrimination of any kind will not be tolerated.

---

## 📄 License

By contributing to ALIVE, you agree that your contributions will be licensed under the same license as the project. Please see the LICENSE file for more details.

---

## 🙏 Thanks

Your contributions make ALIVE better for everyone.  
Whether it's code, docs, tests, or feedback — we appreciate your input and look forward to collaborating with you!

---

## 🔄 Development Workflow

For maintainers and frequent contributors:

1. **Main branch** is always deployable
2. **Feature branches** should be created from main
3. **Hotfix branches** can be created for urgent fixes
4. **Release branches** are created when preparing for releases
5. **All changes** go through pull request review
6. **Squash and merge** is preferred for feature PRs
7. **Rebase and merge** is used for small fixes

---

## 🏗️ Architecture Guidelines

When contributing code:

- **EVA (Python)**: Follow FastAPI best practices, use async/await appropriately
- **Avatar (C#)**: Follow ASP.NET Core patterns, use dependency injection
- **WebSocket**: Maintain backward compatibility with existing message formats
- **Docker**: Keep containers lightweight and secure
- **Environment**: Use environment variables for configuration, never hardcode secrets
