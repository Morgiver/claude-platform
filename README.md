# Main - Orchestrateur Principal

Application principale gérant l'orchestration des modules et agents Claude.

## Installation

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt
```

## Structure

```
main/
├── config/
│   ├── main.yaml          # Configuration principale
│   ├── modules.yaml       # Déclaration modules
│   └── logging.yaml       # Configuration logging
├── src/
│   └── main_app/
│       ├── core/          # Event bus, module loader, resource manager
│       ├── logging/       # Système de logging
│       ├── error_handling/# Strategies retry, webhooks
│       └── threading/     # Process pool, auto-scaling
├── tests/
└── venv/                  # Virtual environment
```

## Fonctionnalités

- **Event Bus**: Message broker interne avec pub/sub
- **Module Loader**: Chargement déclaratif avec hot-reload
- **Logging**: Multi-output (console + fichiers rotatifs), DEBUG level
- **Error Handling**: Circuit breaker + retry strategies + webhooks
- **Threading**: Auto-scaling basé sur RAM/CPU disponibles

## Usage

```bash
# Lancer l'application
python -m main_app

# Tests
pytest

# Linting
ruff check .

# Type checking
mypy src/
```

## Configuration

Les fichiers de configuration YAML se trouvent dans `config/`:
- `main.yaml` - Paramètres généraux
- `modules.yaml` - Modules à charger
- `logging.yaml` - Configuration logging

Les secrets (API keys) sont gérés via variables d'environnement.
