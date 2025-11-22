# Project Brief - main/ (Orchestrateur Modulaire)

**Date**: 2025-11-22
**Version**: ALPHA
**Session**: 001

---

## 1. Vision du Projet

`main/` est l'**orchestrateur central** d'une architecture modulaire. Son rôle est de fournir l'infrastructure de base pour charger, gérer et faire communiquer des modules backend Python de manière isolée et fiable.

### Objectif Principal
Créer une plateforme d'orchestration modulaire robuste avec :
- Chargement déclaratif de modules
- Isolation des modules (processus séparés)
- Communication inter-modules via event bus
- Gestion centralisée des erreurs et du logging
- Auto-scaling basé sur ressources système
- Mode test intégré pour validation de stabilité

---

## 2. Responsabilités de main/

### Core Responsibilities

1. **Module Loading & Management**
   - Chargement déclaratif depuis `config/modules.yaml`
   - Hot-reload sur modification de fichiers (ALPHA: optionnel)
   - Lifecycle management (load/unload/reload)
   - Auto-restart des modules en cas de crash

2. **Event Bus (Message Broker Interne)**
   - Pub/sub pattern pour communication inter-modules
   - Event bus centralisé dans `main/`
   - Modules s'enregistrent comme subscribers
   - Isolation des erreurs (un subscriber qui plante n'affecte pas les autres)

3. **Logging Centralisé**
   - Console + fichiers rotatifs
   - Niveau DEBUG pour ALPHA
   - Format humain
   - Logs par module isolés et traçables

4. **Error Handling**
   - Retry automatique avec exponential backoff
   - Circuit breaker pour services externes
   - Webhooks pour notifications critiques
   - Isolation des erreurs (un module qui plante ne crash pas `main/`)

5. **Threading & Multiprocessing**
   - Process pool avec spawn à la demande
   - Auto-scaling basé sur RAM/CPU disponibles
   - Calcul automatique des limites (ResourceManager)
   - Isolation des modules dans des processus séparés

6. **Resource Management**
   - Monitoring RAM/CPU en temps réel
   - Calcul dynamique des limites de processus/threads
   - Prévention de surcharge système

7. **Mode Test Intégré** ✨ NEW
   - Lancement avec `--test` flag
   - Découverte automatique des tests de tous modules chargés
   - Exécution centralisée via pytest
   - Rapport de stabilité consolidé

---

## 3. Architecture Technique

### Structure des Modules

**Emplacement**: `../modules-backend/mod-*/`

**Interface Standard**:
```python
# Chaque module expose:
def initialize(event_bus, config):
    """Called by main/ on module load"""
    pass

def shutdown():
    """Called by main/ on module unload"""
    pass

# Optional:
def get_tests():
    """Return list of test paths for --test mode"""
    return ["tests/"]
```

### Communication Inter-Modules

```
main/ (Event Bus)
  ├─> mod-A subscribes to "data.received"
  ├─> mod-B publishes "data.received"
  └─> Event Bus delivers event to mod-A
```

**Pattern**: Modules ne se connaissent PAS directement, ils communiquent via events.

### Isolation des Modules

**ALPHA**: Modules chargés dans le même processus (simple, rapide)
**BETA/PRODUCTION**: Modules dans processus séparés (robustesse)

---

## 4. Configuration

### Structure de Configuration

**main/config/main.yaml**
- Paramètres globaux (resource limits, retry strategies, etc.)

**main/config/modules.yaml**
- Liste déclarative des modules à charger
- Configuration spécifique par module
- Enable/disable par module

**main/config/logging.yaml**
- Niveaux de log par module
- Sortie console/fichier
- Rotation des fichiers

### Secrets Management
- Variables d'environnement (`.env`)
- Pas de secrets dans YAML

---

## 5. Mode Test Intégré

### Fonctionnalité

```bash
# Lancer main/ en mode normal
python -m main_app

# Lancer en mode test
python -m main_app --test
```

### Comportement en Mode Test

1. Charger tous les modules déclarés dans `modules.yaml`
2. Appeler `get_tests()` sur chaque module
3. Découvrir tous les tests (pytest discovery)
4. Exécuter la suite complète
5. Générer rapport consolidé
6. Exit code basé sur succès/échec

### Avantages
- Validation de stabilité globale avant déploiement
- Tests de non-régression inter-modules
- CI/CD friendly (exit code)

---

## 6. Objectif Minimal ALPHA v0.1.0-alpha.1

### Démo de Validation

**Scénario**: Charger 2 modules dummy qui communiquent via event bus

**Module A** (Producer):
- Publie event `"test.ping"` avec data `{"message": "hello"}`

**Module B** (Consumer):
- Subscribe à `"test.ping"`
- Log le message reçu

**Success Criteria**:
- Les 2 modules se chargent sans erreur
- Event bus délivre l'event
- Module B reçoit et log le message
- Logs centralisés dans `main/logs/`
- Hot-reload fonctionne (modifier module A → auto-reload)

---

## 7. Contraintes & Décisions Techniques

### Contraintes ALPHA
- **1 classe = 1 fichier** (préférence, pas strict)
- **Max 1500 lignes par fichier** (tolérance ALPHA)
- **Tests**: Validation manuelle OK, tests automatisés bonus
- **Documentation**: Minimale, code auto-documenté

### Décisions Architecturales

| Aspect | Décision | Justification |
|--------|----------|---------------|
| **Module Discovery** | Déclaratif (YAML) | Contrôle explicite, pas de surprises |
| **Hot-reload** | Watchdog | Standard Python, fiable |
| **Event Bus** | In-process (ALPHA) | Simplicité, performance |
| **Process Isolation** | BETA feature | ALPHA focus sur fonctionnalité |
| **Error Strategy** | Circuit breaker + retry | Best practice, évite cascades |
| **Logging** | Rotating files | Gestion auto de la taille |
| **Resource Limits** | Auto-calculés | S'adapte au hardware |
| **Test Mode** | pytest integration | Standard, extensible |

---

## 8. Modules Backend Prévus (Futur)

Liste prévisionnelle des modules qui utiliseront `main/`:

1. `mod-agents/` - Gestion agents Claude (profils, sessions)
2. `mod-agent-sdk/` - Wrapper Claude Agent SDK
3. `mod-communication/` - WebSocket/Redis inter-agents
4. `mod-project-manager/` - CRUD projets/tâches
5. `mod-git-integration/` - Opérations Git/GitHub
6. `mod-code-analysis/` - Analyse statique
7. `mod-testing/` - Exécution tests

**Note**: Ces modules ne concernent PAS `main/` pour l'instant. On focus uniquement sur l'infrastructure d'orchestration.

---

## 9. Non-Objectifs (Out of Scope pour main/)

❌ Interface utilisateur (web/CLI)
❌ Logique métier des agents Claude
❌ Gestion de projets/tâches
❌ Intégration Git/GitHub
❌ Frontend Vue.js

`main/` est **PURE INFRASTRUCTURE**. Les modules apportent la logique métier.

---

## 10. Success Criteria Globaux

### ALPHA Success (v0.1.0 - v0.N.0)
- ✅ Charge N modules déclarés
- ✅ Event bus fonctionne entre modules
- ✅ Hot-reload opérationnel
- ✅ Logs centralisés lisibles
- ✅ Auto-restart sur crash module
- ✅ Mode test valide stabilité
- ✅ Resource manager calcule limites correctement

### BETA Success (Future)
- ✅ Modules isolés en processus séparés
- ✅ Performance optimisée
- ✅ Tests automatisés complets
- ✅ Métriques de monitoring
- ✅ Documentation API complète

---

## 11. Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Module plante et crash main/ | Critique | Isolation processus (BETA), try/except partout (ALPHA) |
| Hot-reload casse état | Moyen | Limiter hot-reload à dev, pas prod |
| Fuite mémoire modules | Moyen | Monitoring RAM, limites par module |
| Event bus surchargé | Moyen | Queue size limits, async processing |

---

## 12. Prochaines Étapes (Workflow)

**Après ce document**:
1. ✅ **Step 2**: @tech-architect → `tech-specifications.md`
2. ✅ **Step 3**: @task-decomposer (ALPHA) → `alpha-tasks/`
3. ✅ **Step 4**: @codebase-scanner → `current-state.md` (code existant)
4. ✅ **Initialize versioning**: v0.1.0-alpha.1
5. 🔄 **Cycle ALPHA**: Mission → Code → Test → Feedback

---

**Document validé**: En attente validation utilisateur
**Prochaine action**: Step 2 (Technical Architecture)
