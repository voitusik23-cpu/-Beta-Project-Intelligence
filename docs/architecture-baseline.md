# Architecture baseline — initial

Статус: частично известен, требует сверки с исходным кодом.

## Известно из текущего контекста
- Desktop/local web application запускается на 127.0.0.1:18762.
- Sidebar содержит Live Radar, New Projects, Early Stages, Testnet & Points, Opportunities, Waitlist, Funded Projects, Late Entry, Monitoring, My Recommendations, Review Queue, Favorites, Archived/Rejected, Project Dossiers, Sources, Settings.
- Dashboard содержит summary cards, discovery feed, source health и recent events.
- Приложение уже содержит базу и результат первичного анализа.
- Отчёт Codex упоминает Python и JavaScript проверки, но точный стек и команды надо подтвердить в рабочей копии.

## Неизвестно — не предполагать
- frontend framework/version;
- backend framework/API;
- database engine/schema;
- migration framework;
- source registry schema;
- scheduler/background worker;
- test commands;
- deployment/release flow;
- app repository URL;
- текущая ветка и commit hash.

## Требование к следующему аудиту
Codex должен заполнить этот документ фактическими данными из исходного кода и приложить пути к конкретным файлам/символам. Не выдумывать архитектуру по одному скриншоту.
