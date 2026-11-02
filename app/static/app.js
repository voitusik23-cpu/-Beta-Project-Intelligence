const $ = selector => document.querySelector(selector);
let allProjects = [], allSources = [], currentView = 'radar';
const savedLanguage = localStorage.getItem('bpiLanguage');
let language = savedLanguage === 'en' ? 'en' : 'ru';

const copy = {
  en: {
    groups: { discover: 'DISCOVER', opportunities: 'OPPORTUNITIES', tracking: 'TRACKING', config: 'CONFIGURATION' },
    nav: { radar: '◉  LIVE RADAR', new: '✦  NEW PROJECTS', incubation: '◈  EARLY INCUBATION', testnet: '⌘  TESTNET & POINTS', waitlist: '◷  WAITLIST', funded: '⬡  FUNDED PROJECTS', late: '↗  LATE ENTRY', myTop: '★  MY TOP PROJECTS', reviewQueue: '☷  REVIEW QUEUE', watchlist: '☆  WATCHLIST', rejected: '▧  DEFERRED / REJECTED', dossiers: '▤  PROJECT DOSSIERS', sources: '⌁  SOURCES', settings: '⚙  SETTINGS' },
    headings: {
      radar: ['Live Radar', 'Early signals across projects, funding, and participation.'],
      new: ['New Projects', 'Recently discovered projects and source signals.'],
      incubation: ['Early Incubation', 'Projects in beta, early access, or early discovery.'],
      waitlist: ['Waitlist', 'Waitlist opportunities surfaced by public sources.'],
      funded: ['Funded Projects', 'Funding dossiers with evidence links. No rumors are marked confirmed.'],
      testnet: ['Testnet & Points', 'Testnet, devnet, points, and quest signals.'],
      late: ['Late Entry', 'Live product and mainnet signals worth checking.'],
      myTop: ['My Top Projects', 'Only projects that passed initial screening, deep review, and evidence verification appear here.'],
      reviewQueue: ['Review Queue', 'Candidates awaiting initial screening or deeper project research.'], rejected: ['Deferred / Rejected', 'Records are retained with reasons; nothing is deleted from the database.'],
      watchlist: ['Watchlist', 'Projects saved for follow-up.'],
      dossiers: ['Project Dossiers', 'All tracked project profiles.'],
      sources: ['Sources', 'Connector health and configuration status.'],
      settings: ['Settings', 'Local storage, evidence handling, and collection options.']
    },
    ui: {
      brand: 'INDEPENDENT WEB3 RADAR', local: '● LOCAL', exportCsv: 'Export CSV', exportJson: 'Export JSON', scan: '↻  Scan sources',
      projects: 'TRACKED PROJECTS', projectsHint: 'Local project dossiers', signals: 'NEW SIGNALS', signalsHint: 'Unique source references',
      waitlists: 'WAITLISTS', waitlistsHint: 'Signals to verify', sources: 'CONNECTED SOURCES', sourcesHint: 'Ready to collect',
      feed: 'DISCOVERY FEED', latest: 'Latest discoveries', search: 'Search projects…', recent: 'Most recent', scoreSort: 'Opportunity score',
      sourceHealth: 'SOURCE HEALTH', connectors: 'Connectors', viewAll: 'View all', changelog: 'CHANGELOG', recentEvents: 'Recent events',
      disclaimer: 'Early signals are leads for manual research. Scores and stages are heuristic, and do not represent investment advice.',
      localDb: 'LOCAL DATABASE ACTIVE', localOnly: 'Data stays on this device', empty: 'No projects yet. Scan connected sources to discover early signals.',
      noFunded: 'No evidence-backed funding records yet. The MVP does not infer funding from rumors.', watchlistEmpty: 'Your watchlist is empty. Open a project dossier and save it to your watchlist.', waitlistEmpty: 'No waitlist signals are currently in the project catalog.', earlyEmpty: 'No early-stage candidates match this view yet.', testnetEmpty: 'No testnet or points candidates match this view yet.', lateEmpty: 'No live or mainnet candidates match this view yet.',
      openWebsite: 'Open project website ↗', openSource: 'Open source link ↗', openGithub: 'Open GitHub repository ↗', websiteMissing: 'No project website found yet; try the source or repository links below.',
      noEvidence: 'No linked source evidence.', noHistory: 'No change history.', noDescription: 'No description yet. Review the source signal and verify details on official channels.',
      translate: 'Translate to Russian', translating: 'Translating…', translationUnavailable: 'Chrome translation is unavailable. Open Google Translate:', originalText: 'Original description',
      sourcePending: 'Source pending', signal: 'Signal:', evidence: 'Evidence', opportunity: 'OPPORTUNITY', participation: 'Participation', cost: 'Cost',
      dossier: 'PROJECT DOSSIER', intelligence: 'Project intelligence', sourceEvidence: 'Source evidence', changeHistory: 'Change history',
      website: 'Website', ecosystem: 'Ecosystem', team: 'Team', teamMissing: 'Not researched yet', funding: 'Funding', fundingMissing: 'No confirmed data. Add only with a direct evidence link.',
      notIdentified: 'Not identified', unknown: 'Unknown', addWatch: 'Add to watchlist', removeWatch: 'Remove from watchlist', firstSeen: 'First seen',
      evidenceLink: 'Evidence', scanDone: 'Scan complete', newSignals: 'new signals', scanFailed: 'Scan failed',
      nothingChanged: 'No changes recorded yet.', projectDiscovered: 'Project discovered', newSourceSignal: 'New source signal',
      localSettings: 'Local data and collection', localSettingsText: 'Data is stored in the project’s folder as SQLite. Set BPI_DATA_DIR to change the database location. Configure extra public RSS URLs in BPI_RSS_FEEDS as a comma-separated list, then restart the app. Enabled RSS and GitHub connectors run in the background at their saved intervals (default 120 minutes); “Scan sources” starts a manual check. Sources that require credentials or access are never polled.',
      evidencePolicy: 'Evidence policy', evidencePolicyText: 'Collected titles and keyword matches are leads for manual verification. Funding, founders, participation requirements, and costs remain unknown until entered with supporting evidence. No wallet actions or automated campaign participation are performed.',
      ready: 'Active', notConfigured: 'Not connected', error: 'Error', runScreen: '☷  Run initial screening', screening: 'Screening…', screenDone: 'Initial screening complete', sourceStatuses: { ACTIVE: 'Active', 'API REQUIRED': 'API required', 'ACCESS REQUIRED': 'Access required', DISABLED: 'Disabled', ERROR: 'Error', 'NEEDS VALIDATION': 'Needs validation', Ready: 'Active', 'Not configured': 'Not connected', Error: 'Error' },
      topEmpty: 'No projects have completed deep review and evidence verification yet. Initial screening keeps candidates in a separate review queue.', topRank: 'Rank', topProject: 'Project', topCategory: 'Category', topStage: 'Stage', topScore: 'Score', topConfidence: 'Confidence', topFunding: 'Funding', topInvestors: 'Investors', topCost: 'Entry cost', topParticipation: 'Participation', topDeadline: 'Deadline', topOpportunity: 'Opportunity', topWebsite: 'Website', topUpdated: 'Updated',
      manualActions: { APPROVED: 'Approve', WATCH: 'Watch', LATER: 'Defer', REJECTED: 'Reject', REVIEWED: 'Mark reviewed' }, reviewNotes: 'My notes', saveNotes: 'Save note', originals: 'Original description', verification: 'Verification', analystConclusion: 'Analyst conclusion', teamIntel: 'Team intelligence', fundingIntel: 'Funding intelligence', technologyIntel: 'Technology intelligence', participationIntel: 'Participation intelligence', opportunityIntel: 'Opportunity analysis', verifiedFacts: 'Reviewed evidence',
      saveSource: 'Save monitoring settings', monitorSource: 'Monitor source', interval: 'Interval (minutes)',
      categories: { Infrastructure: 'Infrastructure', DeFi: 'DeFi', 'AI x Crypto': 'AI x Crypto', Gaming: 'Gaming', Wallet: 'Wallet', 'Developer Tools': 'Developer Tools', Unclassified: 'Unclassified' },
      stages: { Discovered: 'Discovered', Waitlist: 'Waitlist', Testnet: 'Testnet', Participation: 'Participation', Beta: 'Beta', Mainnet: 'Mainnet', Live: 'Live' },
      kinds: { RSS: 'RSS', 'GitHub API': 'GitHub API', Social: 'Social', 'Code hosting': 'Code hosting', Investment: 'Investment', Web: 'Web' }
    },
    sources: {
      'Ethereum Blog RSS': 'Public Ethereum Foundation RSS feed. Project leads are inferred from matching posts.',
      'Ethereum Foundation Ecosystem Support': 'Public ecosystem support RSS feed; may overlap with the other Ethereum feed.',
      'GitHub Repository Search': 'Public unauthenticated API. GitHub rate limits apply.',
      Telegram: 'No Telegram API credentials or channel list configured.',
      'X / Twitter': 'Approved API integration is not configured.', Reddit: 'Official API credentials are not configured.',
      Discord: 'Bot/API integration is not configured.', 'Facebook / Instagram': 'Official API access is not configured.',
      GitLab: 'Connector is not implemented yet.', 'VC portfolios / funding': 'Official portfolio feeds are not configured. Funding is never inferred as confirmed.',
      'Project websites / docs': 'Website crawler is not configured yet.', 'RSS feeds': 'Configure more public RSS feeds with BPI_RSS_FEEDS.'
    },
    eventNotes: {
      'Early-stage signal detected; stage needs verification.': 'Early-stage signal detected; verify the stage.',
      'Waitlist mentioned; verify on official project page.': 'Waitlist mentioned; verify on the official project page.',
      'Testnet/devnet mentioned; verify current availability.': 'Testnet/devnet mentioned; verify that it is currently available.',
      'Points/quest/airdrop mentioned; participation is not verified.': 'Points/quest/airdrop mentioned; participation is not verified.',
      'Beta/early access mentioned; verify eligibility.': 'Beta/early access mentioned; verify eligibility.',
      'Mainnet mentioned; verify product status.': 'Mainnet mentioned; verify product status.'
    }
  },
  ru: {
    groups: { discover: 'ПОИСК', opportunities: 'ВОЗМОЖНОСТИ', tracking: 'ОТСЛЕЖИВАНИЕ', config: 'НАСТРОЙКИ' },
    nav: { radar: '◉  ЖИВОЙ РАДАР', new: '✦  НОВЫЕ ПРОЕКТЫ', incubation: '◈  РАННЯЯ СТАДИЯ', testnet: '⌘  ТЕСТНЕТ И БАЛЛЫ', waitlist: '◷  ЛИСТ ОЖИДАНИЯ', funded: '⬡  С ФИНАНСИРОВАНИЕМ', late: '↗  ПОЗДНИЙ ВХОД', myTop: '★  МОИ РЕКОМЕНДАЦИИ', reviewQueue: '☷  ОЧЕРЕДЬ ПРОВЕРКИ', watchlist: '☆  ИЗБРАННОЕ', rejected: '▧  ОТЛОЖЕННЫЕ / ОТКЛОНЁННЫЕ', dossiers: '▤  ДОСЬЕ ПРОЕКТОВ', sources: '⌁  ИСТОЧНИКИ', settings: '⚙  ПАРАМЕТРЫ' },
    headings: {
      radar: ['Живой радар', 'Ранние сигналы о проектах, финансировании и возможностях участия.'],
      new: ['Новые проекты', 'Недавно обнаруженные проекты и публикации источников.'],
      incubation: ['Ранние стадии', 'Проекты в бета-тесте, раннем доступе или на стадии поиска команды.'],
      waitlist: ['Лист ожидания', 'Наборы в лист ожидания, найденные в открытых источниках.'],
      funded: ['Проекты с финансированием', 'Досье и ссылки на подтверждения. Слухи не считаются подтверждением.'],
      testnet: ['Тестнет и баллы', 'Сигналы о тестнетах, девнетах, баллах и заданиях.'],
      late: ['Можно присоединиться сейчас', 'Работающие продукты и мейннеты, на которые стоит обратить внимание.'],
      myTop: ['Мои рекомендации', 'Здесь появятся только проекты, прошедшие первичный и углублённый анализ с проверенными источниками.'],
      reviewQueue: ['Очередь проверки', 'Кандидаты, ожидающие первичного отбора или углублённой проверки.'], rejected: ['Отложенные и отклонённые', 'Записи сохраняются вместе с причинами — проекты не удаляются из базы.'],
      watchlist: ['Избранное', 'Проекты, сохранённые для дальнейшего изучения.'],
      dossiers: ['Досье проектов', 'Профили всех отслеживаемых проектов.'],
      sources: ['Источники', 'Состояние и настройка подключений.'],
      settings: ['Параметры', 'Локальное хранение, проверка источников и сбор данных.']
    },
    ui: {
      brand: 'НЕЗАВИСИМЫЙ WEB3 РАДАР', local: '● ЛОКАЛЬНО', exportCsv: 'Экспорт CSV', exportJson: 'Экспорт JSON', scan: '↻  Проверить источники',
      projects: 'ПРОЕКТЫ В БАЗЕ', projectsHint: 'Локальные досье проектов', signals: 'НОВЫЕ СИГНАЛЫ', signalsHint: 'Ссылки на источники',
      waitlists: 'ЛИСТЫ ОЖИДАНИЯ', waitlistsHint: 'Сигналы для проверки', sources: 'ИСТОЧНИКИ НА СВЯЗИ', sourcesHint: 'Готовы к сбору',
      feed: 'ЛЕНТА ОБНАРУЖЕНИЙ', latest: 'Последние находки', search: 'Поиск проектов…', recent: 'Сначала новые', scoreSort: 'По оценке возможности',
      sourceHealth: 'СОСТОЯНИЕ ИСТОЧНИКОВ', connectors: 'Подключения', viewAll: 'Все источники', changelog: 'ИЗМЕНЕНИЯ', recentEvents: 'Последние события',
      disclaimer: 'Ранние сигналы — это зацепки для самостоятельной проверки. Оценки и стадии приблизительны и не являются инвестиционной рекомендацией.',
      localDb: 'ЛОКАЛЬНАЯ БАЗА АКТИВНА', localOnly: 'Данные хранятся на этом устройстве', empty: 'Пока проектов нет. Проверьте подключённые источники, чтобы найти ранние сигналы.',
      noFunded: 'Подтверждённых данных о финансировании пока нет. Слухи не используются как доказательство.', watchlistEmpty: 'В избранном пока нет карточек. Откройте досье проекта и добавьте его в избранное.', waitlistEmpty: 'В каталоге пока нет подтверждаемых сигналов о листах ожидания.', earlyEmpty: 'В этой категории пока нет подходящих проектов ранней стадии.', testnetEmpty: 'В этой категории пока нет подходящих тестнетов или программ баллов.', lateEmpty: 'В каталоге пока нет подходящих проектов на стадии мейннета или работающего продукта.',
      openWebsite: 'Открыть сайт проекта ↗', openSource: 'Открыть источник ↗', openGithub: 'Открыть репозиторий GitHub ↗', websiteMissing: 'Сайт проекта пока не найден. Попробуйте открыть источник или репозиторий ниже.',
      noEvidence: 'Ссылок на источники пока нет.', noHistory: 'История изменений пока пуста.', noDescription: 'Описание отсутствует. Изучите источник и проверьте информацию на официальных каналах.',
      translate: 'Перевести на русский', translating: 'Перевод…', translationUnavailable: 'Встроенный перевод Chrome недоступен. Открыть Google Переводчик:', originalText: 'Исходное описание',
      sourcePending: 'Источник не указан', signal: 'Сигнал:', evidence: 'Надёжность', opportunity: 'ОЦЕНКА', participation: 'Участие', cost: 'Стоимость',
      dossier: 'ДОСЬЕ ПРОЕКТА', intelligence: 'Сведения о проекте', sourceEvidence: 'Источники и подтверждения', changeHistory: 'История изменений',
      website: 'Сайт', ecosystem: 'Экосистема', team: 'Команда', teamMissing: 'Пока не изучена', funding: 'Финансирование', fundingMissing: 'Подтверждённых данных нет. Добавляйте только со ссылкой на источник.',
      notIdentified: 'Не найден', unknown: 'Неизвестно', addWatch: 'В избранное', removeWatch: 'Убрать из избранного', firstSeen: 'Впервые найден',
      evidenceLink: 'Подтверждение', scanDone: 'Проверка завершена', newSignals: 'новых сигналов', scanFailed: 'Ошибка проверки',
      nothingChanged: 'Изменений пока нет.', projectDiscovered: 'Проект обнаружен', newSourceSignal: 'Новый сигнал из источника',
      localSettings: 'Локальные данные и сбор', localSettingsText: 'Данные хранятся локально в базе SQLite внутри папки проекта. Путь можно изменить через BPI_DATA_DIR. Дополнительные открытые RSS-ленты задаются через BPI_RSS_FEEDS, после чего приложение нужно перезапустить. Активные RSS и GitHub-коннекторы проверяются в фоне с заданными интервалами (по умолчанию — 120 минут); кнопка «Проверить источники» запускает ручную проверку. Источники, которым нужен API-ключ или доступ, автоматически не опрашиваются.',
      evidencePolicy: 'Как проверяются сведения', evidencePolicyText: 'Заголовки публикаций и совпадения по ключевым словам — это зацепки для ручной проверки. Информация о финансировании, основателях, требованиях и стоимости участия остаётся неизвестной, пока для неё нет подтверждающей ссылки. Приложение не подключает кошельки и не выполняет задания за пользователя.',
      ready: 'Активен', notConfigured: 'Не подключён', error: 'Ошибка', runScreen: '☷  Провести первичный отбор', screening: 'Идёт отбор…', screenDone: 'Первичный отбор завершён', sourceStatuses: { ACTIVE: 'Активен', 'API REQUIRED': 'Нужен API', 'ACCESS REQUIRED': 'Нужен доступ', DISABLED: 'Отключён', ERROR: 'Ошибка', 'NEEDS VALIDATION': 'Нужна проверка', Ready: 'Активен', 'Not configured': 'Не подключён', Error: 'Ошибка' },
      topEmpty: 'Проекты ещё не прошли углублённую проверку и подтверждение фактов. Кандидаты первичного отбора остаются в отдельной очереди.', topRank: 'Место', topProject: 'Проект', topCategory: 'Категория', topStage: 'Стадия', topScore: 'Оценка', topConfidence: 'Достоверность', topFunding: 'Финансирование', topInvestors: 'Фонды', topCost: 'Стоимость входа', topParticipation: 'Участие', topDeadline: 'Срок', topOpportunity: 'Почему интересен', topWebsite: 'Сайт', topUpdated: 'Обновлено',
      manualActions: { APPROVED: 'Одобрить', WATCH: 'В наблюдение', LATER: 'Отложить', REJECTED: 'Исключить', REVIEWED: 'Проверено' }, reviewNotes: 'Мои заметки', saveNotes: 'Сохранить заметку', originals: 'Исходное описание', verification: 'Статус проверки', analystConclusion: 'Вывод аналитика', teamIntel: 'Проверка команды', fundingIntel: 'Проверка финансирования', technologyIntel: 'Проверка технологии', participationIntel: 'Условия участия', opportunityIntel: 'Анализ возможности', verifiedFacts: 'Проверенные источники',
      saveSource: 'Сохранить настройки мониторинга', monitorSource: 'Мониторить источник', interval: 'Интервал (минуты)',
      categories: { Infrastructure: 'Инфраструктура', DeFi: 'DeFi', 'AI x Crypto': 'ИИ и крипто', Gaming: 'Игры', Wallet: 'Кошелёк', 'Developer Tools': 'Инструменты разработчика', Unclassified: 'Не определено' },
      stages: { Discovered: 'Обнаружен', Waitlist: 'Лист ожидания', Testnet: 'Тестнет', Participation: 'Баллы / задания', Beta: 'Бета-тест', Mainnet: 'Мейннет', Live: 'Работает' },
      kinds: { RSS: 'RSS', 'GitHub API': 'GitHub API', Social: 'Соцсети', 'Code hosting': 'Хостинг кода', Investment: 'Инвестиции', Web: 'Веб-сайт' }
    },
    sources: {
      'Ethereum Blog RSS': 'Открытая RSS-лента Ethereum Foundation. Проекты определяются по совпадениям в публикациях.',
      'Ethereum Foundation Ecosystem Support': 'Открытая RSS-лента поддержки экосистемы; публикации могут повторяться в другой ленте Ethereum.',
      'GitHub Repository Search': 'Открытый API без авторизации. Действуют ограничения GitHub на частоту запросов.',
      Telegram: 'Не настроены доступ к API Telegram и список каналов.',
      'X / Twitter': 'Официальное подключение к API не настроено.', Reddit: 'Официальный API Reddit не настроен.',
      Discord: 'Подключение бота или API не настроено.', 'Facebook / Instagram': 'Официальный API не настроен.',
      GitLab: 'Коннектор пока не реализован.', 'VC portfolios / funding': 'Официальные списки портфелей фондов не подключены. Слухи не считаются подтверждённым финансированием.',
      'Project websites / docs': 'Сборщик данных с сайтов пока не настроен.', 'RSS feeds': 'Дополнительные открытые RSS-ленты задаются через BPI_RSS_FEEDS.'
    },
    eventNotes: {
      'Early-stage signal detected; stage needs verification.': 'Найден ранний сигнал; стадию нужно проверить.',
      'Waitlist mentioned; verify on official project page.': 'Упомянут лист ожидания; проверьте его на официальном сайте проекта.',
      'Testnet/devnet mentioned; verify current availability.': 'Упомянут тестнет/девнет; проверьте, доступен ли он сейчас.',
      'Points/quest/airdrop mentioned; participation is not verified.': 'Упомянуты баллы, задания или аирдроп; участие не проверено.',
      'Beta/early access mentioned; verify eligibility.': 'Упомянуты бета-тест или ранний доступ; проверьте условия участия.',
      'Mainnet mentioned; verify product status.': 'Упомянут мейннет; проверьте состояние продукта.'
    }
  }
};

function tr(key) { return copy[language].ui[key] ?? key; }
function safe(value = '') { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function externalHref(value) {
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? safe(url.href) : ''; }
  catch { return ''; }
}
function stageName(value) { return copy[language].ui.stages[value] || value || tr('unknown'); }
function categoryName(value) { return copy[language].ui.categories[value] || value || tr('unknown'); }
function statusName(value) { return copy[language].ui.sourceStatuses[value] || value; }
function kindName(value) { return copy[language].ui.kinds[value] || value; }
function unknownValue(value) {
  if (!value || value === 'Unknown' || value === 'UNKNOWN') return tr('unknown');
  if (language === 'ru' && value === 'Unknown — check official source') return 'Неизвестно — проверьте официальный источник';
  return value;
}
function sourceDetail(source) { return copy[language].sources[source.name] || source.detail || ''; }
function sourceGroupName(value) {
  if (language !== 'ru') return value || '';
  return ({
    'Airdrop aggregators': 'Агрегаторы аирдропов', 'Grants & incubators': 'Гранты и инкубаторы',
    'Investment databases': 'Базы данных инвестиций', 'Investor portfolios': 'Портфели фондов',
    'On-chain analytics': 'Ончейн-аналитика', 'Social platforms': 'Социальные платформы',
    'Technical sources': 'Технические источники', Other: 'Прочее', Telegram: 'Telegram'
  })[value] || value || '';
}
function eventType(value) { return value === 'Project discovered' ? tr('projectDiscovered') : value === 'New source signal' ? tr('newSourceSignal') : value; }
function eventSummary(value) {
  let result = value || '';
  for (const [en, translated] of Object.entries(copy[language].eventNotes)) result = result.replaceAll(en, translated);
  return language === 'ru' ? result.replace('Source: ', 'Источник: ') : result.replace('Источник: ', 'Source: ');
}
function dateTime(value) { try { return new Date(value).toLocaleString(language === 'ru' ? 'ru-RU' : 'en-US'); } catch { return value || ''; } }
function setText(selector, value) { const node = $(selector); if (node) node.textContent = value; }

function translationCacheKey(id, text) {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i++) hash = Math.imul(hash ^ text.charCodeAt(i), 16777619);
  return `bpi.translation.ru.${id}.${hash >>> 0}`;
}

function googleTranslateUrl(text) {
  return `https://translate.google.com/?sl=auto&tl=ru&text=${encodeURIComponent(text)}&op=translate`;
}

async function translateDescription(projectId, original, output, button) {
  if (!original || language !== 'ru') return;
  const key = translationCacheKey(projectId, original);
  const cached = localStorage.getItem(key);
  if (cached) { output.textContent = cached; return; }
  if (!('Translator' in window)) {
    output.innerHTML = `${safe(tr('translationUnavailable'))} <a target="_blank" rel="noopener noreferrer" href="${safe(googleTranslateUrl(original))}">Google Translate ↗</a>`;
    return;
  }
  button.disabled = true;
  button.textContent = tr('translating');
  output.textContent = tr('translating');
  try {
    const translator = await Translator.create({ sourceLanguage: 'en', targetLanguage: 'ru' });
    const translated = await translator.translate(original);
    if (!translated || translated === original) throw Error('Translation returned no result');
    localStorage.setItem(key, translated);
    output.textContent = translated;
    button.hidden = true;
    api(`/api/projects/${projectId}/translation`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ translated_description: translated }) }).catch(() => {});
  } catch (error) {
    output.innerHTML = `${safe(tr('translationUnavailable'))} <a target="_blank" rel="noopener noreferrer" href="${safe(googleTranslateUrl(original))}">Google Translate ↗</a>`;
    button.disabled = false;
    button.textContent = tr('translate');
  }
}

function wireTranslation(button, output, id, original) {
  if (language !== 'ru' || !original) { button.hidden = true; return; }
  const cached = localStorage.getItem(translationCacheKey(id, original));
  if (cached) { output.textContent = cached; button.hidden = true; }
  else button.onclick = () => translateDescription(id, original, output, button);
}

async function renderTopProjects() {
  const c = copy[language].ui;
  try {
    const projects = await api('/api/my-top-projects');
    if (!projects.length) {
      $('#project-list').innerHTML = '';
      $('#empty').textContent = tr('topEmpty');
      $('#empty').classList.remove('hidden');
      $('.project-list').classList.add('hidden');
      return;
    }
    const labels = ['topRank','topProject','topCategory','topStage','topScore','topConfidence','topFunding','topInvestors','topCost','topParticipation','topDeadline','topOpportunity','topWebsite','topUpdated'];
    $('#project-list').innerHTML = `<div class="table-wrap"><table class="top-table"><thead><tr>${labels.map(key => `<th>${safe(c[key])}</th>`).join('')}</tr></thead><tbody>${projects.map((p,i) => `<tr data-id="${p.id}"><td>${i+1}</td><td><button class="table-link" data-open-detail>${safe(p.name)}</button></td><td>${safe(categoryName(p.category))}</td><td>${safe(stageName(p.stage))}</td><td>${p.score}/100</td><td>${p.evidence_confidence}%</td><td>${safe(p.funding_summary || tr('unknown'))}</td><td>${safe(p.investors || tr('unknown'))}</td><td>${safe(p.entry_cost || tr('unknown'))}</td><td>${safe(p.participation_summary || tr('unknown'))}</td><td>${safe(p.deadline || tr('unknown'))}</td><td>${safe(p.opportunity || tr('unknown'))}</td><td>${externalHref(p.website) ? `<a target="_blank" rel="noopener noreferrer" href="${externalHref(p.website)}">${safe(c.topWebsite)} ↗</a>` : safe(tr('notIdentified'))}</td><td>${safe(dateTime(p.updated_at))}</td></tr>`).join('')}</tbody></table></div>`;
    $('#empty').classList.add('hidden');
    $('.project-list').classList.remove('hidden');
    $('#project-list').querySelectorAll('tr[data-id]').forEach(row => {
      row.querySelector('[data-open-detail]').onclick = () => showDetail(row.dataset.id);
      row.querySelectorAll('a').forEach(link => link.onclick = event => event.stopPropagation());
    });
  } catch (error) { toast(`${tr('scanFailed')} · ${error.message}`); }
}

function applyLanguage() {
  const c = copy[language];
  document.documentElement.lang = language;
  $('#language').value = language;
  document.querySelectorAll('[data-nav]').forEach(button => { button.textContent = c.nav[button.dataset.nav]; });
  document.querySelectorAll('[data-group]').forEach(label => { label.textContent = c.groups[label.dataset.group]; });
  setText('#brand-tagline', tr('brand'));
  setText('#live-pill', tr('local'));
  setText('#export-csv', tr('exportCsv'));
  setText('#export-json', tr('exportJson'));
  setText('#screen', tr('runScreen'));
  const scan = $('#scan');
  if (!scan.disabled) scan.textContent = tr('scan');
  const staticLabels = {
    '#metric-label-projects': 'projects', '#metric-hint-projects': 'projectsHint', '#metric-label-signals': 'signals', '#metric-hint-signals': 'signalsHint',
    '#metric-label-waitlists': 'waitlists', '#metric-hint-waitlists': 'waitlistsHint', '#metric-label-sources': 'sources', '#metric-hint-sources': 'sourcesHint',
    '#feed-label': 'feed', '#source-health': 'sourceHealth', '#connectors': 'connectors', '#view-all': 'viewAll', '#changelog-label': 'changelog', '#recent-events': 'recentEvents',
    '#disclaimer': 'disclaimer', '#local-db': 'localDb', '#local-only': 'localOnly'
  };
  for (const [selector, key] of Object.entries(staticLabels)) setText(selector, tr(key));
  $('#search').placeholder = tr('search');
  $('#sort').options[0].text = tr('recent');
  $('#sort').options[1].text = tr('scoreSort');
  const [heading, subtitle] = c.headings[currentView];
  setText('#heading', heading);
  setText('#subheading', subtitle);
  render();
}

async function api(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw Error(await response.text());
  return response.json();
}

function matches(project) {
  if (currentView === 'dossiers') return true;
  if (currentView === 'rejected') return project.level1_status === 'REJECTED' || project.manual_status === 'REJECTED' || project.manual_status === 'LATER';
  if (currentView === 'reviewQueue') return ['PASS', 'REVIEW', 'PENDING'].includes(project.level1_status) && project.level2_status !== 'COMPLETE' && project.manual_status !== 'REJECTED';
  if (currentView === 'watchlist') return !!project.watchlisted && project.manual_status !== 'REJECTED';
  if (project.level1_status === 'REJECTED' || project.manual_status === 'REJECTED' || project.manual_status === 'LATER') return false;
  if (currentView === 'new' || currentView === 'radar') return true;
  if (currentView === 'waitlist') return project.stage === 'Waitlist';
  if (currentView === 'testnet') return ['Testnet', 'Participation'].includes(project.stage);
  if (currentView === 'incubation') return ['Discovered', 'Beta'].includes(project.stage);
  if (currentView === 'late') return ['Mainnet', 'Live'].includes(project.stage);
  if (currentView === 'funded') return (project.funding_count || 0) > 0;
  return true;
}

function renderSources() {
  $('#project-list').innerHTML = allSources.map(source => {
    const supported = (source.kind === 'RSS' && externalHref(source.url)) || source.name === 'GitHub Repository Search';
    const controls = supported ? `<div class="source-settings"><label><input type="checkbox" data-source-enabled ${source.enabled ? 'checked' : ''}> ${safe(copy[language].ui.monitorSource)}</label><label>${safe(copy[language].ui.interval)} <input type="number" data-source-cadence min="15" max="10080" step="15" value="${Math.max(15, source.cadence_minutes || 120)}"></label><button class="button quiet" data-source-save>${safe(copy[language].ui.saveSource)}</button></div>` : '';
    return `<article class="project-card"><div class="card-top"><div><div class="project-name">${safe(source.name)}</div><div class="source-kind">${safe(sourceGroupName(source.source_group || source.kind))}</div><div class="card-description">${safe(sourceDetail(source))}${externalHref(source.url) ? `<br><a target="_blank" rel="noopener noreferrer" href="${externalHref(source.url)}">${safe(source.url)}</a>` : ''}${source.enabled && source.cadence_minutes ? `<br>${language === 'ru' ? 'Интервал: ' : 'Interval: '}${source.cadence_minutes} ${language === 'ru' ? 'мин.' : 'min'}` : ''}${source.last_checked ? `<br>${language === 'ru' ? 'Последняя проверка: ' : 'Last checked: '}${safe(dateTime(source.last_checked))}` : ''}${source.last_run_error ? `<br><span class="status error">${safe(source.last_run_error)}</span>` : ''}</div>${controls}</div><span class="status ${source.status === 'ERROR' || source.status === 'Error' ? 'error' : source.status !== 'ACTIVE' && source.status !== 'Ready' ? 'off' : ''}">● ${safe(statusName(source.status))}</span></div><div class="tag-row"><span class="tag">${safe(kindName(source.kind))}</span><span class="tag">${source.enabled ? (language === 'ru' ? 'Автопроверка включена' : 'Monitoring enabled') : (language === 'ru' ? 'Не собирается автоматически' : 'Not polled automatically')}</span></div></article>`;
  }).join('');
  $('#project-list').querySelectorAll('[data-source-save]').forEach(button => button.onclick = async () => {
    const card = button.closest('.project-card');
    const source = allSources[Array.from(card.parentElement.children).indexOf(card)];
    try {
      await api(`/api/sources/${source.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: card.querySelector('[data-source-enabled]').checked, cadence_minutes: Number(card.querySelector('[data-source-cadence]').value) }) });
      toast(language === 'ru' ? 'Настройки источника сохранены' : 'Source settings saved');
      allSources = await api('/api/sources'); renderSources();
    } catch (error) { toast(`${tr('scanFailed')} · ${error.message}`); }
  });
  $('#empty').classList.add('hidden');
  $('.project-list').classList.remove('hidden');
}

function renderSettings() {
  $('#project-list').innerHTML = `<article class="project-card"><div class="project-name">${safe(tr('localSettings'))}</div><div class="card-description">${safe(tr('localSettingsText'))}</div></article><article class="project-card"><div class="project-name">${safe(tr('evidencePolicy'))}</div><div class="card-description">${safe(tr('evidencePolicyText'))}</div></article>`;
  $('#empty').classList.add('hidden');
  $('.project-list').classList.remove('hidden');
}

function emptyMessage(view) {
  const messages = {
    funded: 'noFunded', watchlist: 'watchlistEmpty', waitlist: 'waitlistEmpty',
    incubation: 'earlyEmpty', testnet: 'testnetEmpty', late: 'lateEmpty'
  };
  return tr(messages[view] || 'empty');
}

function render() {
  setText('#list-title', currentView === 'radar' ? tr('latest') : copy[language].headings[currentView][0]);
  if (currentView === 'sources') return renderSources();
  if (currentView === 'settings') return renderSettings();
  if (currentView === 'myTop') return renderTopProjects();
  if (currentView === 'myTop') return renderTopProjects();
  const query = $('#search').value.toLocaleLowerCase();
  let projects = allProjects.filter(matches).filter(project => !query || `${project.name} ${project.description || ''} ${project.category}`.toLocaleLowerCase().includes(query));
  if ($('#sort').value === 'score') projects.sort((a, b) => b.opportunity_score - a.opportunity_score);
  $('#project-list').innerHTML = projects.map(project => {
    const visitUrl = externalHref(project.website);
    const description = (language === 'ru' && project.translated_description) || project.description || tr('noDescription');
    return `<article class="project-card" data-id="${project.id}"><div class="card-top"><div><div class="project-name">${safe(project.name)}</div><div class="card-description" data-description>${safe(description)}</div><button class="button quiet translate-description" data-translate>${safe(tr('translate'))}</button>${visitUrl ? `<a class="button quiet project-visit" target="_blank" rel="noopener noreferrer" href="${visitUrl}">${safe(tr('openWebsite'))}</a>` : ''}</div><div class="score">${project.opportunity_score}<small> / 100</small><br><small>${safe(tr('opportunity'))}</small></div></div><div class="tag-row"><span class="tag stage">${safe(tr('signal'))} ${safe(stageName(project.stage))}</span><span class="tag">${safe(categoryName(project.category))}</span><span class="tag">${safe(project.source_names || tr('sourcePending'))}</span><span class="tag warn">${safe(tr('evidence'))} ${project.confidence}%</span><span class="tag">${safe(tr('participation'))}: ${safe(unknownValue(project.participation))}</span><span class="tag">${safe(tr('cost'))}: ${safe(unknownValue(project.cost))}</span>${project.level1_status ? `<span class="tag ${project.level1_status === 'REJECTED' ? 'warn' : ''}">${language === 'ru' ? 'Первичная проверка' : 'Initial screen'}: ${safe(project.level1_status)}</span>` : ''}</div></article>`;
  }).join('');
  $('#empty').classList.toggle('hidden', projects.length > 0);
  $('#empty').textContent = emptyMessage(currentView);
  $('.project-list').classList.toggle('hidden', projects.length === 0);
  document.querySelectorAll('.project-card[data-id]').forEach(card => {
    card.onclick = () => showDetail(card.dataset.id);
    card.querySelectorAll('.project-visit').forEach(link => { link.onclick = event => event.stopPropagation(); });
    const project = allProjects.find(item => String(item.id) === card.dataset.id);
    const translateButton = card.querySelector('[data-translate]');
    const description = card.querySelector('[data-description]');
    if (project.translated_description && language === 'ru') translateButton.hidden = true;
    else wireTranslation(translateButton, description, project.id, project.description || '');
    translateButton.onclick = event => { event.stopPropagation(); translateDescription(project.id, project.description || '', description, translateButton); };
  });
}

async function load() {
  const notice = $('#load-notice');
  const retry = $('#load-retry');
  retry.disabled = true;
  const [projectResult, sourceResult, eventResult] = await Promise.allSettled([
    api('/api/projects'), api('/api/sources'), api('/api/events')
  ]);
  if (projectResult.status === 'rejected') {
    setText('#load-notice-text', `${language === 'ru' ? 'Не удалось загрузить проекты' : 'Could not load projects'}: ${projectResult.reason.message || projectResult.reason}`);
    notice.classList.remove('hidden');
    retry.disabled = false;
    throw projectResult.reason;
  }
  allProjects = Array.isArray(projectResult.value) ? projectResult.value : [];
  allSources = sourceResult.status === 'fulfilled' && Array.isArray(sourceResult.value) ? sourceResult.value : [];
  const events = eventResult.status === 'fulfilled' && Array.isArray(eventResult.value) ? eventResult.value : [];
  setText('#metric-projects', allProjects.length);
  setText('#metric-signals', allProjects.reduce((count, project) => count + (project.signal_count || 0), 0));
  setText('#metric-waitlists', allProjects.filter(project => project.stage === 'Waitlist').length);
  setText('#metric-sources', sourceResult.status === 'fulfilled' ? allSources.filter(source => source.status === 'ACTIVE' && source.enabled).length : '—');
  $('#source-mini').innerHTML = [...allSources].sort((a,b) => Number(b.status === 'ACTIVE' && b.enabled) - Number(a.status === 'ACTIVE' && a.enabled)).slice(0, 5).map(source => `<div class="source-row"><div>${safe(source.name)}<div class="source-kind">${safe(kindName(source.kind))}</div></div><span class="status ${source.status === 'ERROR' ? 'error' : source.status !== 'ACTIVE' ? 'off' : ''}">● ${safe(statusName(source.status))}</span></div>`).join('');
  $('#event-list').innerHTML = events.slice(0, 6).map(event => `<div class="event"><b>${safe(event.project_name)} · ${safe(eventType(event.event_type))}</b><p>${safe(eventSummary(event.summary))}</p><time>${safe(dateTime(event.created_at))}</time></div>`).join('') || `<div class="disclaimer">${safe(eventResult.status === 'rejected' ? (language === 'ru' ? 'Лента событий временно недоступна.' : 'The event feed is temporarily unavailable.') : tr('nothingChanged'))}</div>`;
  render();
  const partialFailure = [sourceResult, eventResult].some(result => result.status === 'rejected');
  if (partialFailure) {
    const unavailable = [sourceResult.status === 'rejected' ? (language === 'ru' ? 'источники' : 'sources') : '', eventResult.status === 'rejected' ? (language === 'ru' ? 'лента событий' : 'event feed') : ''].filter(Boolean).join(language === 'ru' ? ' и ' : ' and ');
    setText('#load-notice-text', language === 'ru' ? `Проекты загружены, но временно недоступны: ${unavailable}.` : `Projects loaded, but temporarily unavailable: ${unavailable}.`);
    notice.classList.remove('hidden');
  } else {
    notice.classList.add('hidden');
  }
  retry.disabled = false;
}

async function showDetail(id) {
  const project = await api('/api/projects/' + id);
  const signals = project.signals.map(signal => `<li>${externalHref(signal.url) ? `<a target="_blank" rel="noopener noreferrer" href="${externalHref(signal.url)}">${safe(signal.title || signal.url)}</a>` : safe(signal.title || signal.url)} · ${safe(signal.source_name)} · ${safe(dateTime(signal.discovered_at))}</li>`).join('') || `<li>${safe(tr('noEvidence'))}</li>`;
  const events = project.events.map(event => `<li>${safe(dateTime(event.created_at))} — ${safe(eventType(event.event_type))}: ${safe(eventSummary(event.summary))} ${externalHref(event.evidence_url) ? `<a target="_blank" rel="noopener noreferrer" href="${externalHref(event.evidence_url)}">${safe(tr('evidenceLink'))}</a>` : ''}</li>`).join('') || `<li>${safe(tr('noHistory'))}</li>`;
  const siteUrl = externalHref(project.website);
  const githubSignal = project.signals.find(signal => signal.source_name === 'GitHub Repository Search' && externalHref(signal.url));
  const sourceSignal = project.signals.find(signal => externalHref(signal.url));
  const visitUrl = siteUrl || (githubSignal && externalHref(githubSignal.url)) || (sourceSignal && externalHref(sourceSignal.url));
  const visitLabel = siteUrl ? tr('openWebsite') : githubSignal ? tr('openGithub') : tr('openSource');
  const website = siteUrl ? `<a target="_blank" rel="noopener noreferrer" href="${siteUrl}">${safe(project.website)}</a>` : tr('notIdentified');
  const githubButton = githubSignal && siteUrl ? `<a class="button quiet" target="_blank" rel="noopener noreferrer" href="${externalHref(githubSignal.url)}">${safe(tr('openGithub'))}</a>` : '';
  const review = project.review || {};
  const displayedDescription = (language === 'ru' && review.translated_description) || project.description || tr('noDescription');
  const original = review.translated_description ? `<details class="original-description"><summary>${safe(copy[language].ui.originals)}</summary><p>${safe(project.description || '')}</p></details>` : '';
  const founders = project.founders.length ? project.founders.map(f => `<li>${safe(f.name)}${f.previous_projects ? ` · ${safe(f.previous_projects)}` : ''}${externalHref(f.profile_url) ? ` · <a target="_blank" rel="noopener noreferrer" href="${externalHref(f.profile_url)}">${safe(tr('evidenceLink'))}</a>` : ''}${externalHref(f.evidence_url) ? ` · <a target="_blank" rel="noopener noreferrer" href="${externalHref(f.evidence_url)}">${safe(tr('evidenceLink'))}</a>` : ''}</li>`).join('') : `<li>UNKNOWN — ${safe(tr('teamMissing'))}</li>`;
  const funding = project.funding.length ? project.funding.map(f => `<li>${safe(f.round_type || tr('unknown'))} · ${safe(f.amount || tr('unknown'))} · ${safe(f.date || tr('unknown'))}${f.investor ? ` · ${safe(f.investor)}` : ''} · <a target="_blank" rel="noopener noreferrer" href="${externalHref(f.evidence_url)}">${safe(tr('evidenceLink'))}</a></li>`).join('') : `<li>UNKNOWN — ${safe(tr('fundingMissing'))}</li>`;
  const grants = project.grants.length ? project.grants.map(g => `<li>${safe(g.provider)} · ${safe(g.amount || tr('unknown'))} · ${safe(g.date || tr('unknown'))} · <a target="_blank" rel="noopener noreferrer" href="${externalHref(g.evidence_url)}">${safe(tr('evidenceLink'))}</a></li>`).join('') : `<li>UNKNOWN</li>`;
  const requirements = project.requirements.length ? project.requirements.map(r => `<li>${safe(r.kind)}: ${safe(r.details || tr('unknown'))} · ${safe(r.cost || tr('unknown'))}${externalHref(r.evidence_url) ? ` · <a target="_blank" rel="noopener noreferrer" href="${externalHref(r.evidence_url)}">${safe(tr('evidenceLink'))}</a>` : ''}</li>`).join('') : `<li>${safe(review.participation_summary || 'UNKNOWN')}</li>`;
  const techLinks = project.signals.filter(s => s.source_name === 'GitHub Repository Search').map(s => `<li><a target="_blank" rel="noopener noreferrer" href="${externalHref(s.url)}">${safe(s.title || s.url)}</a> · ${safe(dateTime(s.published_at || s.discovered_at))}</li>`).join('') || `<li>UNKNOWN</li>`;
  const campaigns = project.campaigns.length ? project.campaigns.map(c => `<li>${safe(c.title)} · ${safe(c.kind || tr('unknown'))} · ${safe(c.status || tr('unknown'))}${externalHref(c.url) ? ` · <a target="_blank" rel="noopener noreferrer" href="${externalHref(c.url)}">${safe(tr('evidenceLink'))}</a>` : ''}${c.ends_at ? ` · ${safe(language === 'ru' ? 'До ' : 'Until ')}${safe(c.ends_at)}` : ''}</li>`).join('') : `<li>UNKNOWN</li>`;
  const reviewEvidence = project.review_evidence.length ? project.review_evidence.map(e => `<li><b>${safe(e.field_key)}</b>: ${safe(e.claim)} · ${safe(e.verification_status)} · <a target="_blank" rel="noopener noreferrer" href="${externalHref(e.url)}">${safe(tr('evidenceLink'))}</a></li>`).join('') : `<li>${safe(tr('noEvidence'))}</li>`;
  const conclusion = review.analyst_conclusion ? `<div class="detail-section"><h3>${safe(copy[language].ui.analystConclusion)}</h3><p>${safe(review.analyst_conclusion)}</p><p>${safe(review.opportunity || '')}</p><p>${safe(review.risks || '')}</p><p>${safe(review.score_rationale || '')}</p></div>` : '';
  const actions = Object.entries(copy[language].ui.manualActions).map(([action,label]) => `<button class="button" data-review-action="${action}">${safe(label)}</button>`).join('');
  $('#detail').innerHTML = `<div class="detail-head"><div><div class="eyebrow">${safe(tr('dossier'))} · ${safe(tr('evidence'))} ${project.confidence}%</div><h2>${safe(project.name)}</h2></div><button class="detail-close" aria-label="${language === 'ru' ? 'Закрыть' : 'Close'}">×</button></div><div class="project-actions">${visitUrl ? `<a class="button primary" target="_blank" rel="noopener noreferrer" href="${visitUrl}">${safe(visitLabel)}</a>` : `<span class="disclaimer">${safe(tr('websiteMissing'))}</span>`}${githubButton}</div><p id="detail-description">${safe(displayedDescription)}</p><button class="button quiet" id="detail-translate">${safe(tr('translate'))}</button><div class="tag-row"><span class="tag stage">${safe(tr('signal'))} ${safe(stageName(project.stage))}</span><span class="tag">${safe(categoryName(project.category))}</span><span class="tag">${safe(tr('opportunity'))} ${project.opportunity_score}/100</span><span class="tag">${safe(tr('firstSeen'))} ${safe(dateTime(project.first_seen))}</span>${review.level1_status ? `<span class="tag">Level 1 ${safe(review.level1_status)}</span>` : ''}</div><div class="detail-section"><h3>${safe(tr('intelligence'))}</h3><p>${safe(tr('website'))}: ${website}<br>${safe(tr('ecosystem'))}: ${safe(project.ecosystem || tr('unknown'))}<br>${safe(tr('team'))}: ${safe(review.team_summary || tr('teamMissing'))}<br>${safe(tr('funding'))}: ${safe(review.funding_summary || tr('fundingMissing'))}<br>${safe(tr('participation'))}: ${safe(review.participation_summary || unknownValue(project.participation))} · ${safe(tr('cost'))}: ${safe(review.entry_cost || unknownValue(project.cost))}</p></div><div class="detail-section"><h3>${safe(tr('sourceEvidence'))} (${project.signals.length})</h3><ul>${signals}</ul></div><div class="detail-section"><h3>${safe(tr('changeHistory'))}</h3><ul>${events}</ul></div><div class="detail-section"><button class="button" id="watch">${safe(project.watchlisted ? tr('removeWatch') : tr('addWatch'))}</button></div>`;
  $('#detail').innerHTML = `<div class="detail-head"><div><div class="eyebrow">${safe(tr('dossier'))} · ${safe(tr('evidence'))} ${project.confidence}% · ${safe(review.verification_status || 'UNVERIFIED')}</div><h2>${safe(project.name)}</h2></div><button class="detail-close" aria-label="${language === 'ru' ? 'Закрыть' : 'Close'}">×</button></div><div class="project-actions">${visitUrl ? `<a class="button primary" target="_blank" rel="noopener noreferrer" href="${visitUrl}">${safe(visitLabel)}</a>` : `<span class="disclaimer">${safe(tr('websiteMissing'))}</span>`}${githubButton}</div><p id="detail-description">${safe(displayedDescription)}</p>${original}<button class="button quiet" id="detail-translate">${safe(tr('translate'))}</button><div class="tag-row"><span class="tag stage">${safe(tr('signal'))} ${safe(stageName(project.stage))}</span><span class="tag">${safe(categoryName(project.category))}</span><span class="tag">${safe(tr('opportunity'))} ${project.opportunity_score}/100</span><span class="tag">${safe(tr('firstSeen'))} ${safe(dateTime(project.first_seen))}</span><span class="tag">L1 ${safe(review.level1_status || 'PENDING')}</span><span class="tag">L2 ${safe(review.level2_status || 'NOT STARTED')}</span></div><div class="detail-section"><h3>${safe(tr('intelligence'))}</h3><p>${safe(tr('website'))}: ${website}<br>${safe(tr('ecosystem'))}: ${safe(project.ecosystem || tr('unknown'))}<br>${safe(tr('team'))}: ${safe(review.team_summary || tr('teamMissing'))}<br>${safe(tr('funding'))}: ${safe(review.funding_summary || tr('fundingMissing'))}<br>${safe(tr('participation'))}: ${safe(review.participation_summary || unknownValue(project.participation))} · ${safe(tr('cost'))}: ${safe(review.entry_cost || unknownValue(project.cost))}<br>${safe(copy[language].ui.topScore)}: ${safe(review.score ?? 'UNKNOWN')} / 100 · ${safe(copy[language].ui.topConfidence)}: ${safe(review.evidence_confidence ?? 0)}%</p></div><div class="detail-section"><h3>${safe(copy[language].ui.teamIntel)}</h3><ul>${founders}</ul></div><div class="detail-section"><h3>${safe(copy[language].ui.fundingIntel)}</h3><ul>${funding}${grants}</ul></div><div class="detail-section"><h3>${safe(copy[language].ui.technologyIntel)}</h3><ul>${techLinks}</ul><p>${safe(review.product_summary || 'UNKNOWN')}</p></div><div class="detail-section"><h3>${safe(copy[language].ui.participationIntel)}</h3><ul>${requirements}${campaigns}</ul></div><div class="detail-section"><h3>${safe(copy[language].ui.opportunityIntel)}</h3><p>${safe(review.opportunity || 'UNKNOWN')}<br>${safe(review.risks || 'UNKNOWN')}</p></div>${conclusion}<div class="detail-section"><h3>${safe(copy[language].ui.verifiedFacts)}</h3><ul>${reviewEvidence}</ul></div><div class="detail-section"><h3>${safe(tr('sourceEvidence'))} (${project.signals.length})</h3><ul>${signals}</ul></div><div class="detail-section"><h3>${safe(tr('changeHistory'))}</h3><ul>${events}</ul></div><div class="detail-section"><div class="project-actions">${actions}</div><label for="review-notes">${safe(copy[language].ui.reviewNotes)}</label><textarea id="review-notes" maxlength="12000">${safe(review.user_notes || '')}</textarea> <button class="button" id="save-review-notes">${safe(copy[language].ui.saveNotes)}</button><p class="disclaimer">${safe(review.level1_reason || '')}${review.reject_reason ? `<br>${safe(review.reject_reason)}` : ''}</p></div><div class="detail-section"><button class="button" id="watch">${safe(project.watchlisted ? tr('removeWatch') : tr('addWatch'))}</button></div>`;
  $('#detail').showModal();
  if (review.translated_description && language === 'ru') $('#detail-translate').hidden = true;
  else wireTranslation($('#detail-translate'), $('#detail-description'), project.id, project.description || '');
  $('#detail-translate').onclick = () => translateDescription(project.id, project.description || '', $('#detail-description'), $('#detail-translate'));
  $('#detail').querySelectorAll('[data-review-action]').forEach(button => button.onclick = async () => {
    await api(`/api/projects/${id}/review`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ manual_status: button.dataset.reviewAction }) });
    $('#detail').close(); await load(); await showDetail(id);
  });
  $('#save-review-notes').onclick = async () => {
    await api(`/api/projects/${id}/review`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_notes: $('#review-notes').value }) });
    toast(language === 'ru' ? 'Заметка сохранена' : 'Note saved');
  };
  $('.detail-close').onclick = () => $('#detail').close();
  $('#watch').onclick = async () => { await api('/api/projects/' + id + '/watchlist', { method: 'POST' }); $('#detail').close(); await load(); };
}

function toast(message) {
  $('#toast').textContent = message;
  $('#toast').classList.add('show');
  setTimeout(() => $('#toast').classList.remove('show'), 3500);
}

$('#language').onchange = event => {
  language = event.target.value;
  localStorage.setItem('bpiLanguage', language);
  applyLanguage();
};
$('#scan').onclick = async () => {
  const button = $('#scan');
  button.disabled = true;
  button.textContent = language === 'ru' ? 'Сканирование…' : 'Scanning…';
  try {
    const result = await api('/api/collect', { method: 'POST' });
    const count = result.new_projects_or_signals || 0;
    toast(`${tr('scanDone')} · ${count} ${tr('newSignals')}`);
    await load();
  } catch (error) {
    toast(`${tr('scanFailed')} · ${error.message}`);
  } finally {
    button.disabled = false;
    button.textContent = tr('scan');
  }
};
$('#screen').onclick = async () => {
  const button = $('#screen');
  button.disabled = true;
  button.textContent = tr('screening');
  try {
    const result = await api('/api/review/screen', { method: 'POST' });
    const counts = result.counts || {};
    toast(`${tr('screenDone')} · ${language === 'ru' ? 'Допущено' : 'Pass'}: ${counts.PASS || 0}, ${language === 'ru' ? 'проверить' : 'Review'}: ${counts.REVIEW || 0}, ${language === 'ru' ? 'отложено' : 'Rejected'}: ${counts.REJECTED || 0}`);
    await load();
  } catch (error) { toast(`${tr('scanFailed')} · ${error.message}`); }
  finally { button.disabled = false; button.textContent = tr('runScreen'); }
};
$('#search').oninput = render;
$('#sort').onchange = render;
$('#load-retry').onclick = () => load().catch(error => toast(`${tr('scanFailed')} · ${error.message}`));
$('#nav').onclick = event => {
  const button = event.target.closest('button[data-nav]');
  if (button) setView(button.dataset.nav);
};
document.querySelectorAll('[data-view]').forEach(button => { button.onclick = () => setView(button.dataset.view); });
function setView(view) {
  currentView = view;
  document.querySelectorAll('nav button[data-nav]').forEach(button => button.classList.toggle('active', button.dataset.nav === view));
  const [heading, subtitle] = copy[language].headings[view];
  setText('#heading', heading);
  setText('#subheading', subtitle);
  render();
}
try {
  applyLanguage();
} catch (error) {
  setText('#load-notice-text', `${language === 'ru' ? 'Ошибка настройки интерфейса' : 'Interface setup error'}: ${error.message || error}`);
  $('#load-notice').classList.remove('hidden');
}
load().catch(error => toast(`${tr('scanFailed')} · ${error.message}`));
