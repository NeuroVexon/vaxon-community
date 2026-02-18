# Third-Party Licenses

Axon by NeuroVexon uses the following open-source libraries.
This document lists all direct dependencies and their licenses.

## Backend (Python)

| Package | Version | License | Usage |
|---------|---------|---------|-------|
| [FastAPI](https://github.com/tiangolo/fastapi) | 0.109.0 | MIT | Web Framework |
| [Uvicorn](https://github.com/encode/uvicorn) | 0.27.0 | BSD-3-Clause | ASGI Server |
| [python-multipart](https://github.com/andrew-d/python-multipart) | 0.0.6 | Apache-2.0 | File Upload Parsing |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | 2.0.25 | MIT | ORM / Database |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.19.0 | MIT | Async SQLite |
| [Pydantic](https://github.com/pydantic/pydantic) | 2.5.3 | MIT | Data Validation |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | 2.1.0 | MIT | Settings Management |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.0.0 | BSD-3-Clause | .env Files |
| [httpx](https://github.com/encode/httpx) | >= 0.27.0 | BSD-3-Clause | HTTP Client |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | >= 1.10.0 | Apache-2.0 | OpenAI API Client |
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | >= 0.40.0 | MIT | Claude API Client |
| [google-genai](https://github.com/googleapis/python-genai) | >= 1.0.0 | Apache-2.0 | Gemini API Client |
| [NumPy](https://github.com/numpy/numpy) | >= 1.26.0 | BSD-3-Clause | Vector Calculations |
| [python-jose](https://github.com/mpdavis/python-jose) | 3.3.0 | MIT | JWT / Cryptography |
| [passlib](https://github.com/glic3rern/passlib) | 1.7.4 | BSD-3-Clause | Password Hashing |
| [cryptography](https://github.com/pyca/cryptography) | 42.0.0 | Apache-2.0 / BSD-3-Clause | Encryption |
| [python-dateutil](https://github.com/dateutil/dateutil) | 2.8.2 | Apache-2.0 / BSD-3-Clause | Date Parsing |
| [APScheduler](https://github.com/agronholm/apscheduler) | 3.10.4 | MIT | Task Scheduling |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | 1.23.8 | AGPL-3.0 * | PDF Processing |
| [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | 4.2 | MIT | Web Search |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | 21.0 | LGPL-3.0 | Telegram Bot |
| [discord.py](https://github.com/Rapptz/discord.py) | 2.3.2 | MIT | Discord Bot |

> \* **PyMuPDF (AGPL-3.0)**: Used for PDF text extraction during document upload.
> The AGPL-3.0 requires source code disclosure for network usage.
> Since Axon Community Edition is open source under Apache-2.0, this condition is fulfilled.
> For proprietary deployments, Artifex offers commercial licenses.

> **python-telegram-bot (LGPL-3.0)**: The LGPL allows usage in proprietary
> software as long as the library itself is not modified and is dynamically linked.
> Axon uses the library unmodified as a dependency.

## Frontend (TypeScript/JavaScript)

| Package | Version | License | Usage |
|---------|---------|---------|-------|
| [React](https://github.com/facebook/react) | ^18.2.0 | MIT | UI Framework |
| [React DOM](https://github.com/facebook/react) | ^18.2.0 | MIT | DOM Rendering |
| [React Router DOM](https://github.com/remix-run/react-router) | ^6.22.0 | MIT | Routing |
| [Lucide React](https://github.com/lucide-icons/lucide) | ^0.323.0 | ISC | Icons |
| [clsx](https://github.com/lukeed/clsx) | ^2.1.0 | MIT | CSS Classes |
| [i18next](https://github.com/i18next/i18next) | ^25.8.10 | MIT | Internationalization |
| [react-i18next](https://github.com/i18next/react-i18next) | ^16.5.4 | MIT | React i18n Bindings |
| [Vite](https://github.com/vitejs/vite) | ^5.0.12 | MIT | Build Tool |
| [TypeScript](https://github.com/microsoft/TypeScript) | ^5.3.3 | Apache-2.0 | Type System |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | ^3.4.1 | MIT | CSS Framework |
| [ESLint](https://github.com/eslint/eslint) | ^8.56.0 | MIT | Linting |
| [PostCSS](https://github.com/postcss/postcss) | ^8.4.35 | MIT | CSS Processing |
| [Autoprefixer](https://github.com/postcss/autoprefixer) | ^10.4.17 | MIT | CSS Vendor Prefixes |
| [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react) | ^4.2.1 | MIT | Vite React Plugin |

## CLI (Python)

| Package | Version | License | Usage |
|---------|---------|---------|-------|
| [Typer](https://github.com/tiangolo/typer) | >= 0.9.0 | MIT | CLI Framework |
| [httpx](https://github.com/encode/httpx) | >= 0.27.0 | BSD-3-Clause | HTTP Client |
| [Rich](https://github.com/Textualize/rich) | >= 13.0.0 | MIT | Terminal Output |

## License Summary

| License | Package Count | Compatible with Apache-2.0 |
|---------|---------------|---------------------------|
| MIT | 22 | Yes |
| BSD-3-Clause | 6 | Yes |
| Apache-2.0 | 5 | Yes |
| ISC | 1 | Yes |
| LGPL-3.0 | 1 | Yes (unmodified) |
| AGPL-3.0 | 1 | Yes (open source) * |

> \* The AGPL-3.0 of PyMuPDF is compatible since Axon Community Edition itself
> is open source under Apache-2.0. For proprietary/closed forks, a commercial
> PyMuPDF license must be obtained or PyMuPDF must be replaced with an alternative
> (e.g., `pdfplumber`, MIT).

---

As of: 2026-02-17 | Axon v2.0.0
