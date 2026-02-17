# Third-Party Licenses

Axon by NeuroVexon nutzt die folgenden Open-Source-Bibliotheken.
Dieses Dokument listet alle direkten Dependencies und ihre Lizenzen auf.

## Backend (Python)

| Paket | Version | Lizenz | Verwendung |
|-------|---------|--------|------------|
| [FastAPI](https://github.com/tiangolo/fastapi) | 0.109.0 | MIT | Web-Framework |
| [Uvicorn](https://github.com/encode/uvicorn) | 0.27.0 | BSD-3-Clause | ASGI Server |
| [python-multipart](https://github.com/andrew-d/python-multipart) | 0.0.6 | Apache-2.0 | File Upload Parsing |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | 2.0.25 | MIT | ORM / Database |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.19.0 | MIT | Async SQLite |
| [Pydantic](https://github.com/pydantic/pydantic) | 2.5.3 | MIT | Datenvalidierung |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | 2.1.0 | MIT | Settings Management |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0.0 | BSD-3-Clause | .env Dateien |
| [httpx](https://github.com/encode/httpx) | >= 0.27.0 | BSD-3-Clause | HTTP Client |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | >= 1.10.0 | Apache-2.0 | OpenAI API Client |
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | >= 0.40.0 | MIT | Claude API Client |
| [google-genai](https://github.com/googleapis/python-genai) | >= 1.0.0 | Apache-2.0 | Gemini API Client |
| [NumPy](https://github.com/numpy/numpy) | >= 1.26.0 | BSD-3-Clause | Vektor-Berechnungen |
| [python-jose](https://github.com/mpdavis/python-jose) | 3.3.0 | MIT | JWT / Kryptografie |
| [passlib](https://github.com/glic3rern/passlib) | 1.7.4 | BSD-3-Clause | Passwort-Hashing |
| [cryptography](https://github.com/pyca/cryptography) | 42.0.0 | Apache-2.0 / BSD-3-Clause | Verschluesselung |
| [python-dateutil](https://github.com/dateutil/dateutil) | 2.8.2 | Apache-2.0 / BSD-3-Clause | Datums-Parsing |
| [APScheduler](https://github.com/agronholm/apscheduler) | 3.10.4 | MIT | Task-Scheduling |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | 1.23.8 | AGPL-3.0 * | PDF-Verarbeitung |
| [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | 4.2 | MIT | Web-Suche |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | 21.0 | LGPL-3.0 | Telegram Bot |
| [discord.py](https://github.com/Rapptz/discord.py) | 2.3.2 | MIT | Discord Bot |

> \* **PyMuPDF (AGPL-3.0)**: Wird fuer PDF-Text-Extraktion bei Dokument-Upload genutzt.
> Die AGPL-3.0 erfordert bei Netzwerk-Nutzung die Offenlegung des Quellcodes.
> Da Axon Community Edition unter Apache-2.0 Open Source ist, ist diese Bedingung erfuellt.
> Fuer proprietaere Deployments bietet Artifex kommerzielle Lizenzen an.

> **python-telegram-bot (LGPL-3.0)**: Die LGPL erlaubt die Nutzung in proprietaerer
> Software, solange die Bibliothek selbst nicht modifiziert wird und dynamisch gelinkt ist.
> Axon nutzt die Bibliothek unmodifiziert als Dependency.

## Frontend (TypeScript/JavaScript)

| Paket | Version | Lizenz | Verwendung |
|-------|---------|--------|------------|
| [React](https://github.com/facebook/react) | ^18.2.0 | MIT | UI-Framework |
| [React DOM](https://github.com/facebook/react) | ^18.2.0 | MIT | DOM-Rendering |
| [React Router DOM](https://github.com/remix-run/react-router) | ^6.22.0 | MIT | Routing |
| [Lucide React](https://github.com/lucide-icons/lucide) | ^0.323.0 | ISC | Icons |
| [clsx](https://github.com/lukeed/clsx) | ^2.1.0 | MIT | CSS-Klassen |
| [i18next](https://github.com/i18next/i18next) | ^25.8.10 | MIT | Internationalisierung |
| [react-i18next](https://github.com/i18next/react-i18next) | ^16.5.4 | MIT | React i18n Bindings |
| [Vite](https://github.com/vitejs/vite) | ^5.0.12 | MIT | Build-Tool |
| [TypeScript](https://github.com/microsoft/TypeScript) | ^5.3.3 | Apache-2.0 | Typisierung |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | ^3.4.1 | MIT | CSS-Framework |
| [ESLint](https://github.com/eslint/eslint) | ^8.56.0 | MIT | Linting |
| [PostCSS](https://github.com/postcss/postcss) | ^8.4.35 | MIT | CSS-Processing |
| [Autoprefixer](https://github.com/postcss/autoprefixer) | ^10.4.17 | MIT | CSS Vendor-Prefixes |
| [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react) | ^4.2.1 | MIT | Vite React Plugin |

## CLI (Python)

| Paket | Version | Lizenz | Verwendung |
|-------|---------|--------|------------|
| [Typer](https://github.com/tiangolo/typer) | >= 0.9.0 | MIT | CLI-Framework |
| [httpx](https://github.com/encode/httpx) | >= 0.27.0 | BSD-3-Clause | HTTP Client |
| [Rich](https://github.com/Textualize/rich) | >= 13.0.0 | MIT | Terminal-Ausgabe |

## Lizenz-Zusammenfassung

| Lizenz | Anzahl Pakete | Kompatibel mit Apache-2.0 |
|--------|---------------|---------------------------|
| MIT | 22 | Ja |
| BSD-3-Clause | 6 | Ja |
| Apache-2.0 | 5 | Ja |
| ISC | 1 | Ja |
| LGPL-3.0 | 1 | Ja (unmodifiziert) |
| AGPL-3.0 | 1 | Ja (Open Source) * |

> \* Die AGPL-3.0 von PyMuPDF ist kompatibel, da Axon Community Edition selbst
> Open Source unter Apache-2.0 ist. Fuer proprietaere/geschlossene Forks muss
> eine kommerzielle PyMuPDF-Lizenz erworben oder PyMuPDF durch eine Alternative
> (z.B. `pdfplumber`, MIT) ersetzt werden.

---

Stand: 2026-02-17 | Axon v2.0.0
