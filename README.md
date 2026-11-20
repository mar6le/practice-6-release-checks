# Gateway · контроль випуску Python-сервісу

Bottle обслуговує два маршрути через Waitress. `/health` повертає 200 та `status: available` або 503 у режимі `maintenance`. `/version` повертає `commit`, який у зібраному в CI образі відповідає SHA вихідного коміту.

## Підготовка та запуск

~~~bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-qa.txt
docker build --build-arg BUILD_REF=local.m6 -t practice6-gateway-m6:local .
docker compose up -d --wait --wait-timeout 22
~~~

`HTTP_PORT` задає порт контейнера, `LOCAL_PORT` — опублікований порт, `GATEWAY_IMAGE` — джерело образу. Ідентифікатор випуску й режим готовності передаються сервісу через змінні `BUILD_REF` і `SERVICE_STATE`.

## Перевірки

~~~bash
python -m pytest -q qa
python -m pytest -q runtime --hosts="docker://$(docker compose ps -q gateway)"
python ci/http_check.py 8196 local.m6
docker compose logs gateway
~~~

Після відкриття або оновлення PR до `main` GitHub Actions запускає тести та збирає образ. Запуск для `main` передає зібраний образ завданню розгортання через артефакт. Розгортання використовує Linux VM, GitHub Container Registry, Docker Compose, Testinfra й HTTP-перевірки. Після успішної перевірки образ отримує тег `approved`. Під час збою відновлюється попередній digest, а помилка початкової спроби залишається в загальному статусі запуску.

## Експерименти

У **Gateway qualification** виберіть **Run workflow** у гілці `main`. Вибір `unit-fail` підставляє коміт із навмисно неправильною відповіддю в тесті. Вибір `unavailable` розгортає образ із режимом `maintenance`. Перед цим має бути хоча б один успішний випуск. В Actions зберігаються JUnit XML і журнали, включаючи логи кандидатів, якщо їхні контейнери були створені.

~~~bash
gh workflow run main.yml --ref main -f case=unit-fail
gh workflow run main.yml --ref main -f case=unavailable
~~~

## Відновлення вручну

Для приватного образу спочатку виконайте вхід у GHCR з доступом до читання пакета. Замініть позначення попереднього образу на дійсний digest, а SHA — на повний хеш відповідного коміту.

~~~bash
export GATEWAY_IMAGE=ghcr.io/mar6le/practice-6-release-checks@sha256:PREVIOUS_DIGEST
docker compose pull gateway
docker compose up -d --force-recreate --wait --wait-timeout 22
python ci/http_check.py 8196 PREVIOUS_COMMIT_SHA
docker compose down
~~~

## Навчальна VM

Контейнер запускається на Linux VM GitHub Actions на час прогону, а перевірений образ залишається в реєстрі. На IaaS можна запустити Compose і скрипт на постійній Linux VM, де команда оновлює ОС, Docker та код. На PaaS образ можна передати керованому контейнерному сервісу, де провайдер оновлює середовище. Команда відповідає за залежності образу та його конфігурацію. Витрати визначають тривалість роботи VM або сервісу, місце для образів і логів та вихідний трафік.
