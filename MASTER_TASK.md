# MASTER TASK — Beta Project Intelligence

Версия: 1.0 | Дата фиксации контекста: 2026-11-02

## 1. Продуктовая цель
Развивать уже существующее приложение Beta Project Intelligence. Это не новый проект с нуля и не просто airdrop scraper. Это исследовательская система, которая обнаруживает ранние Web3-проекты, проверяет качество и условия участия, изучает финансирование, команды и технологии и формирует обоснованные рекомендации.

Работать только в существующей рабочей копии приложения. Этот GitHub-репозиторий — центр управления задачами и документацией, пока пользователь отдельно не подтвердит перенос исходного кода.

## 2. Исходная точка из отчёта Codex
По отчёту, показанному пользователем 2026-11-02:
- первичный разбор базы: 291 проект;
- 3 проекта прошли первичную проверку;
- 23 оставлены на ручной проверке;
- 265 отправлены в архив с причиной;
- создано 26 карточек рабочей очереди;
- все 26 карточек получили русские описания;
- MY TOP PROJECTS: 0 проектов;
- два досье заполнены со статусом PARTIALLY VERIFIED и оценками ниже порога;
- подключены три источника: Ethereum Blog RSS, Ethereum Foundation RSS и GitHub Search;
- остальные источники зарегистрированы, но доступ/подключение не подтверждены;
- Python и JavaScript проверки из отчёта прошли.

Это сведения из отчёта агента, а не независимая приёмка. Повторно сверить с реальной БД, файлами и логами. Не изменять данные ради совпадения с отчётом.

## 3. Первый приоритет: UI и отображение данных
Подробное задание: tasks/01-ui-redesign-and-data-visibility.md.

Визуальное направление:
- глубокий графитовый / почти чёрный сине-нейтральный фон;
- панели и карточки светлее фона, с заметным, но сдержанным контрастом;
- один основной акцент: electric lime или cyan; не использовать много конкурирующих цветов;
- активная навигация, важные состояния и ключевые действия используют акцент;
- современная типографика уровня Inter, Geist или IBM Plex Sans; локальный шрифт или безопасный fallback;
- читаемые размеры, контраст, межстрочные интервалы и аккуратная плотность;
- профессиональная аналитическая станция, не игровой neon dashboard;
- единый стиль для всех экранов, таблиц, форм, пустых состояний и модальных окон;
- сохранить русскую локализацию и текущую информационную архитектуру.

Критический дефект для исследования: главная панель показывает пустые/нулевые счётчики и пустую ленту, хотя отчёт говорит о 291 проекте, 26 карточках и 12 источниках (только 3 подключены). Выяснить источник истины, причины несовпадения, проверить фильтры, API, сериализацию, состояния загрузки, ошибки запросов и mapping полей. Исправлять только после определения root cause. Не показывать фиктивные значения.

## 4. Возможности продукта

### Discovery
Находить stealth/formation/pre-launch, incubation/accelerators, waitlist/email signup/invite-only, private/public beta, testnet/devnet, points/quests/retroactive, grants/ecosystem programs и late-entry в действующие кампании.

### Deep research
Исследовать команду и прошлые проекты основателей; инвесторов, фонды, раунды, суммы и даты; grants/incubators/ecosystem backing; продукт, технологии, сеть; GitHub, releases, commits и developer activity; контракты и on-chain activity; пользователей, интеграции, репутацию, риски и качество доказательств.

### Participation intelligence
Для каждого проекта выяснять email, wallet, signature, social accounts, Discord, Telegram, quests/tasks, транзакции, gas, hardware, платные подписки, deposit, KYC, geo/account restrictions, дедлайны, текущую доступность и late-entry. Указывать стоимость, время, сложность и риски. Неподтверждённые условия маркировать как неизвестные.

### Dossier
Русскоязычное досье: описание, категория, стадия, официальный сайт/каналы, команда, funding/investors/grants с источниками, продукт и техническая активность, условия участия/расходы/дедлайны/ограничения, риски, Opportunity Score, Evidence Confidence, дата проверки и источники.

## 5. Списки и навигация
MY TOP PROJECTS; EARLY INCUBATION; WAITLIST; FUNDED PROJECTS; TESTNET & POINTS; LATE ENTRY; WATCHLIST; REJECTED / ARCHIVED. Не дублировать существующие разделы без аудита.

## 6. Фильтрация и рейтинг
- Level 1: проверить весь пул, убрать дубли, мусор, неактуальные и очевидно опасные записи; сохранять причины.
- Level 2: deep research примерно 100 лучших кандидатов, если данных достаточно.
- Итоговая цель — около 30 сильных рекомендаций, допустимо 20–50. Если качественных меньше — показывать меньше.

Согласованные ранее веса, не менять без отдельного разрешения:
- funding 20;
- team 15;
- product 15;
- free entry 15;
- technical activity 10;
- early stage 10;
- docs 5;
- ecosystem potential 10.

Категории: 90–100 VERY HIGH PRIORITY; 80–89 HIGH PRIORITY; 70–79 INTERESTING; 60–69 WATCHLIST; ниже 60 LOW PRIORITY. Evidence Confidence — отдельный показатель. Слабая доказательная база не компенсируется высоким Opportunity Score. Рейтинг не является прогнозом доходности.

## 7. Источники и доверие
A — официальные первичные источники; B — специализированные базы/аналитические агрегаторы; C — социальные/комьюнити источники; D — промо/непроверенные источники.

Направления: official websites/docs/blogs/RSS/release notes; GitHub/GitLab; DeFiLlama Raises, RootData, CryptoRank Funding; официальные VC/grants/incubator/ecosystem pages; Telegram, X, Reddit, Discord только в рамках доступных API и правил платформ; Etherscan, Solscan, Arbiscan, BaseScan, Dune и другие on-chain источники.

Seed sources для проверки:
- https://t.me/s/incrypted_airdrops
- https://t.me/s/cryptototem_official
- https://t.me/airdropinsideryt
- https://t.me/s/airdropquests
- https://www.airdroptracker.io/
- https://sourcechain.org/events/launch/
- https://airdroplet.com/testnet-airdrops
- https://cryptorank.io/drophunting
- https://incrypted.com/airdrops/
- https://airdrops.io/
- https://defillama.com/raises
- https://www.rootdata.com/
- https://cryptorank.io/funding-rounds
- https://coinmarketlab.com/vcs
- https://www.web3.com/portfolio
- https://ethereum.org/community/grants
- https://esp.ethereum.foundation/
- https://solana.org/grants-funding
- https://arbitrum.foundation/grants
- https://www.karmahq.org/funding-map
- https://fundswap.pro/grants
- https://grants.fogofi.com/

Это кандидаты для проверки, а не гарантия доступности или подключения. Проверять актуальность, ToS/API policy, rate limits и ограничения на AI/data processing. Не заявлять, что источник подключён, пока интеграция реально не проверена.

## 8. Мониторинг и контроль
Ежедневный возобновляемый мониторинг; сохранять промежуточные результаты; дедуплицировать сигналы; сохранять историю изменений рейтинга. Никакой автоматической регистрации, wallet connection, signature или транзакций.

## 9. Итоговая таблица
Rank, Project, Category, Stage, Score, Confidence, Funding, Investors, Entry Cost, Participation, Deadline, Opportunity, Website, Updated. Website — кликабельная официальная ссылка. Описания и выводы — на русском.

## 10. Очередь реализации
1. Аудит существующего приложения, данных, источников и текущего состояния.
2. Безопасный backup / фиксация git status.
3. UI redesign и устранение дефекта отображения данных.
4. Проверка Source Registry и фактического health интеграций.
5. Проверка Discovery / dedup / pipeline / resumability.
6. Проверка досье, scoring и evidence confidence.
7. Первый полный анализ по этапам.
8. Тесты, ручная приёмка, итоговый отчёт.

Работать поэтапно. Не переписывать всё за один проход. После каждого этапа фиксировать отчёт и доказательства.
