# Contributing to Axon

Danke, dass du zu Axon beitragen möchtest! Dieses Dokument erklärt, wie du mitmachen kannst.

## Code of Conduct

Bitte lies unseren [Code of Conduct](CODE_OF_CONDUCT.md) bevor du beiträgst.

## Wie kann ich beitragen?

### Bug Reports

1. Prüfe zuerst, ob der Bug bereits gemeldet wurde
2. Erstelle ein neues Issue mit dem "Bug Report" Template
3. Beschreibe das Problem so detailliert wie möglich:
   - Erwartetes Verhalten
   - Tatsächliches Verhalten
   - Schritte zur Reproduktion
   - Screenshots (wenn hilfreich)
   - System-Informationen

### Feature Requests

1. Prüfe, ob das Feature bereits vorgeschlagen wurde
2. Erstelle ein neues Issue mit dem "Feature Request" Template
3. Beschreibe:
   - Das Problem, das du lösen möchtest
   - Deine vorgeschlagene Lösung
   - Alternativen, die du in Betracht gezogen hast

### Pull Requests

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/mein-feature`)
3. Committe deine Änderungen (`git commit -m 'Add: Mein neues Feature'`)
4. Push zum Branch (`git push origin feature/mein-feature`)
5. Öffne einen Pull Request

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

### Mit Docker

```bash
docker-compose up -d
```

## Code Standards

### Python (Backend)

- Python 3.11+
- Type Hints für alle Funktionen
- Docstrings für öffentliche Funktionen
- Formatierung mit Black
- Linting mit Ruff
- Tests mit pytest

```bash
# Formatieren
black backend/

# Linting
ruff check backend/

# Tests
pytest backend/tests/
```

### TypeScript (Frontend)

- TypeScript strict mode
- Functional Components mit Hooks
- Tailwind CSS für Styling
- ESLint für Linting

```bash
# Linting
npm run lint

# Type Check
npm run type-check
```

### Commit Messages

Wir verwenden konventionelle Commit-Messages:

- `feat:` Neues Feature
- `fix:` Bug Fix
- `docs:` Dokumentation
- `style:` Formatierung (kein Code-Change)
- `refactor:` Code-Refactoring
- `test:` Tests hinzufügen/ändern
- `chore:` Maintenance

Beispiele:
```
feat: Add web search tool
fix: Correct file path validation
docs: Update installation guide
```

## Branch Naming

- `feature/` - Neue Features
- `fix/` - Bug Fixes
- `docs/` - Dokumentation
- `refactor/` - Refactoring

## Pull Request Prozess

1. Stelle sicher, dass alle Tests bestehen
2. Aktualisiere die Dokumentation wenn nötig
3. Der PR wird von mindestens einem Maintainer reviewed
4. Nach Approval wird der PR gemergt

## Lizenz

Mit deinem Beitrag stimmst du zu, dass dein Code unter der [Business Source License 1.1](LICENSE) veröffentlicht wird.

## Fragen?

- GitHub Discussions für allgemeine Fragen
- GitHub Issues für Bugs und Features
- Email: contribute@neurovexon.de

---

Vielen Dank für deinen Beitrag! 🚀
