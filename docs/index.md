# Auth & 2FA OTP API — Product & System Spec (OneDoc)

> Версия: 0.1 • Статус: Draft • Владелец: <ФИО/роль> • Дата: <YYYY-MM-DD>  
> Связанные артефакты: [OpenAPI](./api/openapi.yml) · [Диаграммы](./flows/sequence.md) · [ADR](./adr/README.md) · [Тест-матрица](./testing/acceptance.md)

## 0. Executive Summary (One-pager)

**Проблема/Цель.** Нужен безопасный вход в мобильный кошелёк с двухфакторной аутентификацией (OTP) и выдачей краткоживущего JWT для доступа к API.  
**Ключевые решения.** 2FA через OTP (SMS/e-mail / опц. TOTP), Authorization Code + PKCE, `access_jwt` (ES256/EdDSA) + ротационный `refresh_token`, опц. DPoP для привязки к устройству, JWKS для валидации.  
**Scope In.** `/auth/start`, `/auth/otp/verify`, `/oauth/token` (code/refresh), `/auth/logout`, `/auth/logout/all`, `/.well-known/jwks.json`.  
**Scope Out.** Соц-логины, Web-SSO, KYC.  
**Риски.** SIM-swap/перехват SMS, повторное использование refresh, перегрев OTP-провайдера.  
**Definition of Done.** Рабочие флоу логина/refresh/logout; OpenAPI 3.1; метрики/алерты; негативные сценарии покрыты.

---

## 1. Контекст и цели (PRD)

- **Персоны/сегменты.** Пользователи кошелька (iOS/Android), в т.ч. unprivileged клиенты без банковских apps.
- **KPI.** Конверсия логина, P95 «время до токена», доля успешных OTP, отказов по rate-limit.
- **UX-флоу (high-level).** Ввод идентификатора → получение OTP → ввод кода → доступ к продукту. Повторная отправка — ограничена.
- **Политики.** TTL OTP 2–5 мин; 1-разовый; попытки проверки 5–10; resend ≤ 3/10 мин; блокировка и разморозка по правилам.
- **Зависимости.** OTP-провайдер(ы), локализация сообщений, хранение секретов.

## 2. Область работ (Scope)

**Входит.** Старт логина, отправка/валидация OTP, выдача токенов, refresh-rotation (reuse-detect), logout (current & all), JWKS.  
**Не входит.** Соц-логин, Web-SSO, профильный бекофис, изменение номера телефона/e-mail.

## 3. Глоссарий

`OTP`, `challenge_id`, `auth_code`, `access_token`, `refresh_token`, `JWKS`, `DPoP`, `sid`, `acr/amr`.

---

## 4. Бизнес-правила (BR)

| ID  | Правило | Причина/цель |
|-----|---------|--------------|
| BR-1 | OTP одноразовый, TTL ≤ 5 мин | Снижение риска подбора |
| BR-2 | Resend ≤ 3 раз/10 мин; Verify попыток ≤ 10 | Анти-абьюз |
| BR-3 | Refresh — ротационный; reuse → отзыв семьи | Безопасность |
| BR-4 | Logout All отзывает все активные refresh | Управление сессиями |
| BR-5 | Не логировать PII и сам OTP | Конфиденциальность |

---

## 5. Функциональные требования (FR) — с приёмкой

**FR-1. `POST /auth/start`** — создать challenge и отправить OTP.  
*Приёмка:* успех → 200 с `challenge_id`, `expires_in`, `resend_at`; при лимите → 429 и `retry_after`; аудит-событие.

**FR-2. `POST /auth/otp/verify`** — проверить OTP, выдать одноразовый `auth_code` (TTL ≤ 60 c).  
*Приёмка:* верный/непросроченный → 200 с `auth_code`; повтор → 400 `code_redeemed`; просрочка → 400 `otp_expired`.

**FR-3. `POST /oauth/token` (authorization_code + PKCE)** — обмен кода на `access_jwt` + `refresh_token`.  
*Приёмка:* подпись JWT валидна по JWKS; `amr` включает `otp`; корректные `iss/aud/exp`.

**FR-4. `POST /oauth/token` (refresh_token)** — ротация refresh.  
*Приёмка:* старый refresh становится использованным; повторный запрос старым → `token_reused` и отзыв семьи.

**FR-5. `POST /auth/logout` / `POST /auth/logout/all`** — отзыв текущей/всех сессий.  
*Приёмка:* последующие ресурсные вызовы → 401; аудит-событие.

---

## 6. Нефункциональные требования (NFR)

- **Производительность:** P95 `/auth/start` ≤ X ms, `/oauth/token` ≤ Y ms.  
- **Доступность:** SLO ≥ 99.9% для критичных эндпоинтов.  
- **Наблюдаемость:** метрики (успех/отказы/latency), логи без PII, трассировка, `traceId` в ошибках.  
- **Локализация:** RU/EN (расширяемо).  
- **Конфигурация:** лимиты/TTL через feature-flags.

---

## 7. API сводка (детали — в OpenAPI)

| Method | Path                        | Назначение |
|--------|-----------------------------|------------|
| POST   | `/auth/start`              | Старт логина, отправка OTP |
| POST   | `/auth/otp/verify`         | Валидация OTP → `auth_code` |
| POST   | `/oauth/token`             | Code→Tokens (PKCE) / Refresh |
| POST   | `/auth/logout`             | Логаут текущей сессии |
| POST   | `/auth/logout/all`         | Глобальный логаут |
| GET    | `/.well-known/jwks.json`   | JWKS ключи |

---

## 8. Данные/модель

- **Сущности:** `Challenge` (id, идентификатор пользователя, канал, ttl, попытки), `OtpAttempt`, `Session` (`sid`, device), `RefreshFamily` (root, статус), `AuditEvent`.  
- **Индексы:** по пользователю, по `challenge_id`, по `sid`, по `jti` (JWT id) при необходимости.

---

## 9. Безопасность

- **JWT:** ES256/EdDSA; claims: `iss, aud, sub, iat, exp, jti, sid, acr/amr`.  
- **Refresh rotation + reuse detect**; реестр ревокаций.  
- **Sender-constraining (опц.).** DPoP: заголовок `DPoP` с JWS на каждый запрос.  
- **Rate-limit/anti-bruteforce.** По IP/устройству/пользователю; капча/заморозка.  
- **PII.** Не логировать OTP/секреты; маскировать чувствительное.

---

## 10. Последовательности и состояния

См. диаграммы: [Sequences](flows/sequence.md), [States](flows/states.md).

---

## 11. Ошибки (RFC7807)

Формат `application/problem+json`: `type`, `title`, `status`, `code`, `traceId`, `hint`.  
Типовые коды: `otp_invalid`, `otp_expired`, `rate_limited`, `code_redeemed`, `token_reused`, `invalid_dpop`, `token_expired`, `invalid_grant`.

---

## 12. Тест-стратегия и приёмка

- **Позитив:** happy-path для всех FR.  
- **Негатив/abuse:** неверный/просроченный OTP; resend/verify-лимиты; reuse auth_code; reuse refresh; DPoP mismatch; шторм по OTP-провайдеру.  
- **DoD:** функционал, метрики/алерты, дока/руткозы, OpenAPI валиден.

---

## 13. Развёртывание и миграции

Фичефлаги, поэтапная выкладка, rollback, ротация JWKS, key-rollover план.

## 14. Зависимости и интеграции

OTP-провайдер(ы), секрет-хранилище, очередь уведомлений, мониторинг.

## 15. Риски и допущения

Таблица рисков с приоритетом и планом реагирования (SIM-swap, задержки, деградация провайдера).

## 16. Трассируемость

Матрица BR → FR → API → Тесты (ID-связки).

## 17. ADR / Decision Log

Короткие записи решений: алгоритм подписи, TTL, лимиты, политика reuse.

## 18. Словарь и ссылки

Определения, внешние стандарты.

## 19. Changelog и согласование

История изменений, список согласований (роль → статус → дата).
