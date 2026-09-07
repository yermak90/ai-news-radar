# AI News Radar

Telegram-бот, который мониторит AI-новости из нескольких источников, удаляет дубли,
классифицирует материалы по направлениям, оценивает практическую ценность и раз в
день присылает компактный аналитический дайджест. Полное техническое задание — в
[`PRD.md`](./PRD.md).

## Возможности

- Сбор новостей из RSS/Atom-блогов, GitHub Releases, Hacker News (Algolia API) и arXiv API.
- Извлечение содержимого страницы, нормализация URL/заголовков.
- 4-уровневая дедупликация (точный URL → нормализованный заголовок → хэш контента →
  легковесное семантическое сходство) с выбором первичного источника по приоритету
  (Official > Research > Community > Media).
- Дешёвая keyword-фильтрация перед дорогим LLM-вызовом (cost control).
- AI-классификация и анализ через абстракцию `LLMProvider` со строго структурированным
  JSON-ответом (см. `app/ai/schemas.py`), с защитой от prompt injection в системном промпте.
  Реализации: `GeminiProvider` (Google Gemini, `responseMimeType=application/json` +
  `responseSchema`), `OpenAIProvider` (любой OpenAI-совместимый `chat.completions` API,
  `response_format: json_schema`) и `MockLLMProvider` (офлайн keyword-эвристика).
- Скоринг, ранжирование (настраиваемая формула) и diversity-aware выбор TOP 3.
- Ежедневный дайджест + 10 команд Telegram по категориям.
- Планировщик (APScheduler): периодический сбор + ежедневная отправка дайджеста в
  таймзоне `Asia/Almaty` (настраивается), с защитой от повторной отправки в один день.

## Архитектура

```
app/
├── bot/            # Telegram-интерфейс (aiogram 3): handlers, formatters — без бизнес-логики
├── collectors/      # RSS/GitHub/HackerNews/arXiv коллекторы
├── extractors/       # normalize_url/normalize_title/content_hash, HTML-экстракция
├── deduplication/    # 4-уровневый дедупликатор + primary source selection
├── ai/                # LLMProvider abstraction, pydantic-схемы, промпты
├── services/           # collection/processing/ranking/digest/pipeline — вся бизнес-логика
├── repositories/       # доступ к БД (SQLAlchemy 2.x async)
├── models/              # ORM-модели + enum'ы
├── scheduler/            # APScheduler jobs
├── config/                # pydantic-settings, логирование
└── main.py                 # точка входа, склеивает всё вместе
```

Бизнес-логика не знает о Telegram: `services/*` можно вызывать и тестировать
независимо от бота (см. `tests/integration/test_processing_pipeline.py`).

## Быстрый старт (Docker)

1. Создайте Telegram-бота через [@BotFather](https://t.me/BotFather) и получите `TELEGRAM_BOT_TOKEN`.
2. Скопируйте `.env.example` в `.env` и заполните минимум:
   ```env
   TELEGRAM_BOT_TOKEN=<ваш токен>
   ADMIN_TELEGRAM_USER_ID=<ваш числовой Telegram user id, для /refresh>
   ```
3. (Опционально, но рекомендуется) укажите LLM-провайдера. Рекомендуемый вариант —
   Google Gemini, у которого есть щедрый бесплатный тир:
   1. Откройте [aistudio.google.com](https://aistudio.google.com), войдите с Google-аккаунтом.
   2. Нажмите **Get API key** → **Create API key** и скопируйте ключ.
   3. Впишите его в `.env`:
      ```env
      LLM_PROVIDER=gemini
      LLM_API_KEY=<ваш ключ из AI Studio>
      LLM_MODEL=gemini-2.0-flash
      ```
   Вместо Gemini можно использовать любой OpenAI-совместимый API:
   ```env
   LLM_PROVIDER=openai
   LLM_API_KEY=<ваш API-ключ>
   LLM_MODEL=gpt-4o-mini
   ```
   Если оставить `LLM_PROVIDER=mock` (или `LLM_API_KEY` пустым), бот полностью
   работает без реального LLM API — см. раздел "Что замокано" ниже.
4. Запустите:
   ```bash
   docker compose up -d --build
   ```
   Это поднимет PostgreSQL, применит миграции Alembic и запустит бота.
5. Откройте бота в Telegram, выполните `/start`, затем `/refresh` (только для
   `ADMIN_TELEGRAM_USER_ID`), чтобы сразу запустить сбор новостей, не дожидаясь
   расписания. Через несколько секунд-минут выполните `/today`.
6. Дальше дайджест будет приходить автоматически каждый день в `DIGEST_HOUR:DIGEST_MINUTE`
   по таймзоне `TIMEZONE` (по умолчанию `08:00 Asia/Almaty`), а сбор новостей — каждые
   `COLLECTION_INTERVAL_MINUTES` минут (по умолчанию 180).

> Примечание: сборка Docker-образа не проверялась внутри среды разработки этой сессии
> (в песочнице агента нет доступа к Docker daemon), но `Dockerfile`/`docker-compose.yml`
> следуют стандартному паттерну для Python+Postgres приложений и используют то же
> `pyproject.toml`, что уже установлено и протестировано локально. Если при первом
> запуске что-то не соберётся — сначала проверьте `docker compose logs app`.

## Локальный запуск без Docker

Требуется Python 3.12+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# для локального прототипа можно использовать SQLite вместо Postgres:
# DATABASE_URL=sqlite+aiosqlite:///./ai_news_radar.db

alembic upgrade head
python -m app.main
```

## Тесты

```bash
source .venv/bin/activate
pytest -q          # 77 тестов: unit + integration, без обращений к реальному LLM/Telegram API
ruff check app tests
```

Тесты используют изолированную in-memory SQLite БД и `MockLLMProvider` — реальный
LLM API и реальный Telegram API в тестах не задействуются (PRD §62).

## Что реально работает, а что замокано

Это честный MVP: часть требований PRD принципиально невозможно проверить без
реальных внешних credentials (Telegram bot token, LLM API key) и без доступа в
интернет из среды разработки, где собирался этот проект. Ниже — что именно.

### Работает "из коробки", без единого реального ключа

- Вся бизнес-логика pipeline (сбор → извлечение → дедупликация → фильтрация →
  классификация → анализ → скоринг → ранжирование → дайджест) — покрыта тестами
  и реально исполняется на моках.
- `MockLLMProvider` (`LLM_PROVIDER=mock`, значение по умолчанию) — детерминированный
  keyword-based анализатор. Он не обращается ни к какому внешнему API, но
  реализует полный интерфейс `LLMProvider.analyze()` и возвращает валидную
  структурированную схему (категории, recommendation, priority, все scores).
  Так бот может собирать, дедуплицировать и присылать дайджест вообще без LLM-ключа —
  просто с более простой, эвристической аналитикой вместо настоящей LLM.
- Все Telegram-команды, форматирование карточек, разбиение сообщений на части
  по лимиту 4096 символов.
- Планировщик и защита от повторной отправки дайджеста в один день.

### Требует реального ключа, чтобы заработать по-настоящему

- **`TELEGRAM_BOT_TOKEN`** — без него бот вообще не стартует (это проверяется в
  `app/main.py`: явное сообщение в лог вместо падения с непонятной ошибкой).
- **`LLM_API_KEY`** (при `LLM_PROVIDER=gemini` или `openai`) — без него анализ новостей
  будет выполняться эвристикой `MockLLMProvider`, а не настоящей LLM. Значит, `Summary`,
  `Why it matters`, `Practical use` и т.д. будут значительно проще/грубее, чем
  того требует PRD §16.
  - `GeminiProvider` — настоящий клиент Google Gemini API
    (`generativelanguage.googleapis.com`) со structured JSON output
    (`responseMimeType=application/json` + `responseSchema`). Бесплатный ключ —
    на [aistudio.google.com](https://aistudio.google.com) ("Get API key"), см. раздел
    "Быстрый старт" выше.
  - `OpenAIProvider` — настоящий клиент OpenAI-совместимого `chat.completions` API
    со structured JSON output (`response_format: json_schema`) и работает с любым
    OpenAI-совместимым эндпоинтом (Azure OpenAI, локальный vLLM/Ollama, OpenRouter —
    через `LLM_API_BASE`).
  - Оба провайдера используют один и тот же системный промпт с защитой от prompt
    injection (PRD §51) и одну и ту же JSON-схему ответа (`app/ai/provider.py:JSON_SCHEMA`).

### Не проверено вживую (нет сетевого доступа из песочницы разработки)

Среда, в которой собирался этот проект, не имеет общего доступа в интернет
(доступны только несколько сервисных доменов вроде PyPI/npm — не внешние сайты
компаний). Поэтому:

- **RSS-адреса блогов компаний** (OpenAI, Anthropic, Google AI, Meta AI, NVIDIA,
  GitHub Changelog) в `app/db/seed_sources.py` — это URL, известные из документации/
  общих знаний на момент написания кода, но **не провалидированные живым запросом**.
  Компании довольно часто меняют структуру своих сайтов и RSS-путь. Это не ломает
  приложение: `RSSCollector` для конкретного источника просто залогирует ошибку и
  вернёт 0 новостей для этого источника, а остальные источники продолжат работать
  как обычно (PRD §46 — сбой одного источника не должен ронять остальные, это
  покрыто тестом `test_raises_on_http_error`+обработкой в `collection_service.py`).
  **Что делать:** если после `/refresh` какой-то официальный блог не появляется в
  `/models`/`/testing` и т.д. — откройте блог в браузере, найдите актуальный RSS-URL
  (обычно `<site>/feed`, `<site>/rss.xml` или ищите `<link rel="alternate"
  type="application/rss+xml">` в HTML) и обновите `feed_url` в `SEED_SOURCES`
  (`app/db/seed_sources.py`) или прямо в БД через таблицу `sources`.
- Источники с высокой уверенностью в правильности URL — они используют
  официальные, стабильные, документированные API, а не угадываемые blog-пути:
  **arXiv API**, **Hacker News Algolia Search API**, **GitHub REST API
  (Releases)** для DeepSeek/Qwen/Mistral/Meta(через сообщество)/Microsoft
  AutoGen/Hugging Face Transformers/llama.cpp/vLLM/LangChain/NVIDIA TensorRT-LLM.
  Эти 12 источников формата GitHub Releases + arXiv + Hacker News гарантированно
  дают ≥5 рабочих источников даже если все blog RSS-адреса окажутся устаревшими —
  Acceptance Criteria §63.3 ("материалы минимум из 5 источников") выполняется
  и в худшем случае.
- Полный `docker compose up -d` end-to-end запуск с реальным ботом и реальным
  Postgres — не запускался вживую в этой сессии (нет доступа к Docker daemon в
  среде разработки). Структура `Dockerfile`/`docker-compose.yml` стандартна для
  Python 3.12 + Postgres 16 + Alembic; `pip install .` и весь код уже проверены
  локальным venv-окружением (тот же `pyproject.toml`).

## Переменные окружения

См. `.env.example`. Ключевые:

| Переменная | Назначение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота из @BotFather. Обязателен. |
| `ADMIN_TELEGRAM_USER_ID` | Telegram user id, которому доступна `/refresh`. |
| `DATABASE_URL` | Async SQLAlchemy URL. По умолчанию — Postgres (docker-compose), можно SQLite для локального прототипа. |
| `LLM_PROVIDER` | `gemini` (Google Gemini), `openai` (любой OpenAI-совместимый API) или `mock` (без ключа, по умолчанию в коде). |
| `LLM_API_KEY`, `LLM_MODEL`, `LLM_API_BASE` | Настройки LLM-провайдера. Для Gemini ключ — на [aistudio.google.com](https://aistudio.google.com). |
| `TIMEZONE` | Таймзона для дайджеста и cron-расписания. По умолчанию `Asia/Almaty`. |
| `DIGEST_HOUR`, `DIGEST_MINUTE` | Время ежедневной отправки дайджеста, в `TIMEZONE`. |
| `COLLECTION_INTERVAL_MINUTES` | Частота фонового сбора новостей. |
| `LOG_LEVEL` | Уровень логирования. |

Секреты нигде не хардкожены в коде и не закоммичены — `.env` в `.gitignore`.

## Миграции

```bash
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

## Команды бота

`/start` `/help` `/today` `/top` `/stt` `/meeting` `/agents` `/coding` `/rag`
`/enterprise` `/models` `/testing` `/refresh` (только админ, запускает сбор+анализ
вручную и присылает краткую статистику).

## Известные упрощения MVP (осознанные, документированные)

- Semantic similarity (уровень 4 дедупликации) реализован как лёгкий token-Jaccard
  overlap, а не через embeddings/LLM — этого достаточно для MVP и не требует
  дополнительных платных вызовов (PRD прямо допускает такой вариант в §13.1).
- Primary source для кластера выбирается один раз, в момент первого AI-анализа;
  более авторитетный источник, пришедший позже, добавляется как related source,
  но не переписывает уже сгенерированный анализ — это осознанный компромисс
  cost control (не платить за повторный анализ) vs. идеальной точности.
- Inline-кнопки 👍/👎 (PRD §57) не реализованы — PRD явно разрешает вынести это
  за рамки MVP; таблица `news_items` спроектирована так, что фичу легко добавить позже.
