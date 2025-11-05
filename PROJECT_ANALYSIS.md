# Project Analysis — ASOUD Backend

## 1) Quick summary

- Project name: ASOUD Web Services (backend)
- Primary purpose: A Django-based, multi-tenant e-commerce / marketplace backend providing product/catalog management, multi-vendor marketplace, orders, cart, payments, SMS, chat (channels), affiliate system, analytics, and many operational utilities.
- Primary languages & frameworks: Python 3.9+; Django 4.2.x; Django REST Framework; Django Channels (ASGI); Redis (caching/channel layers); PostgreSQL (primary DB in production).
- Repo layout (high level):
  - `config/` — Django project configuration (settings per-env, urls, asgi)
  - `apps/` — Django apps (feature modules: product, market, users, cart, payment, sms, chat, reserve, analytics, etc.)
  - `manage.py`, `Dockerfile*`, `docker-compose*.yaml`, `requirements*.txt`, `pyproject.toml`
  - `utils/`, `templates/`, `static/`, `media/`, numerous audit/test/analysis scripts in repo root


## 2) Architecture & major components

- Web/API layer: Django + DRF exposing REST endpoints under `/api/` (drf_spectacular used for schema). Authentication uses token/JWT-like custom code (`apps.users.authentication.JWTAuthentication`).
- Real-time layer: Django Channels + Daphne and `channels_redis` for production channel layers.
- Persistence: PostgreSQL (primary) with SQLite fallback for development. Models located in each `apps/*/models.py`.
- Caching & messaging: Redis used for channels and caching. Celery-like tasks are referenced (some settings), but Celery is used in dev as eager mode.
- Payments: Integrated through `apps.payment` (payment core classes and gateway wrappers for Zarinpal, Mellat, Parsian mentioned).
- SMS: `apps.sms` implements SMS patterns and handlers and exposes SMS APIs.
- Frontend contract: OpenAPI / Postman artifacts included in repo; typical endpoints: `/api/auth/`, `/api/products/`, `/api/cart/`, `/api/payments/`, `/api/chat/`.


## 3) Key config & constants

- `config/settings/base.py` — primary settings file, registers many `INSTALLED_APPS`, configures logging, REST_FRAMEWORK defaults, Channels, caching, and security defaults.
- `config/settings/development.py` and `production.py` — environment-specific overrides. Production requires `DJANGO_SECRET_KEY` and loads `.env` and `allowed_hosts.json`.
- `pyproject.toml` — small (black config); authoritative dependency lists are in `requirements.txt` and `requirements-dev.txt`.
- `Dockerfile`, `Dockerfile.development`, `Dockerfile.production` and `docker-compose.*.yaml` define containerization and service composition.


## 4) Core apps and responsibilities (high-level)

- apps.core — common utilities: base view classes (`BaseAPIView`, BaseList/Create/Update/Delete), caching helpers, custom exception handler `custom_exception_handler`, serializer helpers, and performance/optimization utilities.
- apps.users — custom `User` model (mobile-number as username), authentication helpers (JWTAuthentication), user profile and bank info models, serializers, views and URL routes.
- apps.product — product models, serializers (owner/marketer), views and urls for product CRUD and marketing features.
- apps.market — marketplace and market-related models (market owners, shares, workflows), plus market-level APIs.
- apps.cart — cart and order models and logic.
- apps.payment — payment models, payment core logic and gateway integrations.
- apps.sms — SMS sending, templates, bulk/pattern handling.
- apps.chat — chat models and channels routing/consumers.
- apps.notification — notification templates, consumers and background processors.
- apps.reserve — reservation system for services/owners (scheduling, specialists).
- apps.analytics — user session tracking and analytics models used by auth/session code.
- apps.* many other smaller feature apps (discount, affiliate, wallet, referral, advertise, etc.) each follow Django app conventions.


## 5) Code patterns & conventions found

- Many apps use `apps.<name>.models`, `apps.<name>.serializers`, `apps.<name>.views`, and `apps.<name>.urls` (split into `owner`, `user`, `admin` where relevant).
- `apps.core.base_views.BaseAPIView` and derived classes are used to enforce consistent API success/error structure via `ApiResponse`.
- Custom `ApiResponse` objects and `apps.core.exception_handler.custom_exception_handler` centralize response/enhanced error structure.
- Serializers include many `Secure*Field` implementations in `apps.core.serializers` enforcing sanitization and validators (reduces repetitive validation code).
- Settings are split per environment in `config/settings` and use environment variables heavily.
- Many management/utility scripts exist in repo root (`setup_test_data.py`, `complete_database_seeder.py`, `postgresql_seeder.py`, security/performance validation scripts). These are useful for CI or audits but are separate from main app runtime.


## 6) Dependency graph (partial, mermaid)

The following is a high-level module interaction diagram (simplified):

```mermaid
flowchart TD
  subgraph DjangoProject
    Config["config (settings, urls, asgi)"]
    Apps["apps/* (feature apps)"]
  end

  Config -->|routes| Apps
  Apps -->|models| Postgres[(PostgreSQL)]
  Apps -->|cache & channels| Redis[(Redis)]
  Apps -->|payments| PaymentGateways((Zarinpal/Mellat/Parsian))
  Apps -->|sms| SMSProvider[(SMS Service)]
  Apps -->|real-time| Channels["Django Channels (ASGI)"]

  Apps -->|uses| Core["apps.core (base views, exception handling, caching)"]
  Apps -->|uses| Users["apps.users (User model & auth)"]
  PaymentGateways -->|interact| Wallet["apps.wallet"]
  Users -->|session logs| Analytics["apps.analytics"]

  classDef infra fill:#f9f,stroke:#333,stroke-width:1px
  Postgres,Redis,PaymentGateways,SMSProvider,Channels class infra
```

Notes: This diagram is intentionally simplified; see module map section for file-level relationships (next).


## 7) File/module map (sample & approach)

- `config/urls.py` imports many app `urls` modules; `config/asgi.py` imports websocket routing from `apps.chat.routing` and `apps.notification`.
- `apps/core` provides `base_views`, `exception_handler`, `caching` used by many apps (e.g., `apps.notification.views` imports `BaseCreateView`).
- `apps/users` is used widely (e.g., `apps.product.models` imports `apps.users.models.User`).
- Recommendation: use a small script (or the existing `test_all_apis.py` style code) to programmatically extract a full import graph. I can produce that script next if you want.


## 8) Important constants and config locations

- Security and authentication: `AUTH_USER_MODEL` in `config/settings/base.py` -> `users.User`.
- REST defaults: `REST_FRAMEWORK` in `base.py` (auth classes, pagination, throttle rates, exception handler override).
- Caches: `CACHES` configured optionally using `django_redis`; falls back to locmem.
- Channels: `CHANNEL_LAYERS` uses `channels_redis` in production else in-memory.


## 9) Observations, potential improvements, and refactors

High-level suggestions (low-risk first):

1. Centralize common validators/utilities
   - There's a `config.validators` module already; continue consolidating app-specific validators/utilities to reduce duplication.

2. Reduce settings duplication and enforce secrets management
   - Keep production-only secrets out of repo; ensure `.env` or secret store is used and documented in `DEPLOYMENT.md`.

3. Add typed interfaces and small unit tests for critical utility functions
   - E.g., `apps.core.caching`, `apps.users.authentication` — add tests for token blacklisting and session management.

4. Improve import graphs & decouple heavy cross-app imports
   - Some apps import lots of other apps (tight coupling). Introduce service-layer APIs or facades for cross-cutting operations (e.g., wallet operations via `apps.wallet.core` instead of direct model imports).

5. Performance/DB optimization
   - Verify that view & queryset code uses `select_related`/`prefetch_related` where appropriate (I saw `apps/core/database_optimization.py` and index migration guides — run those audits programmatically).

6. Logging & observability
   - The base logging config is present; consider structured logging (JSON) for production and ensure Sentry or equivalent is integrated for error aggregation.

7. Tests & CI
   - There's a large battery of test/validation scripts. Convert a subset into proper unit tests (pytest or Django test runner) and add CI job to run them.


## 10) Low-risk extension ideas (how to extend with minimal changes)

- Add a `read-only` public API that exposes product and market listings: implement new DRF viewsets using existing serializers and `BaseListView` to avoid changing models.
- Add a reporting endpoint in `apps.analytics` that aggregates existing `UserSession` and `apps.payment` entries.
- Add feature flags: small middleware and a `FeatureFlag` model to toggle new features without code changes.


## 11) Next steps I can take (pick any):

- Produce a complete import/dependency graph (file-level) and export as `module_graph.dot` or a mermaid map.
- Generate a list of all API endpoints and their HTTP methods (there are scripts in repo; I can run a targeted extractor).
- Create targeted unit tests for `apps.users.authentication` and `apps.core.exception_handler` and run them.
- Add a `CODEBASE_SUMMARY.md` per app (automatically generated: classes, functions, file purposes).


---

If you'd like, I can now:
- (A) Generate a file-level import graph (mermaid) across all `apps/*` modules,
- (B) Extract all API endpoints and produce a concise endpoint inventory,
- (C) Generate per-app summaries (automated) listing models, serializers, views and key methods.

Tell me which of (A/B/C) to run next (or ask for everything), and I'll proceed automatically and update the todo list accordingly.