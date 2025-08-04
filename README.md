# rosstat-population-scraper

Инструмент для автоматической выгрузки данных о численности населения населённых пунктов из [паспортов муниципальных образований на сайте Росстата](https://rosstat.gov.ru/scripts/db_inet2/passport/munr.aspx?base=munst04).

## Функции
- Парсит список районов и населённых пунктов
- Позволяет исключить ненужные районы
- Выбирает нужные годы
- Сохраняет данные в Excel: `выгрузка_2024.xlsx`, `выгрузка_2023.xlsx` и т.д.

## Как использовать
1. Установите зависимости:
   ```bash
   pip install selenium pandas openpyxl beautifulsoup4
   ```
2. Скачайте [ChromeDriver](https://chromedriver.chromium.org/) и поместите в PATH.
3. Запустите:
   ```bash
   python scraper.py
   ```

## Планы
- [ ] Переписать без браузера (`requests` + `BeautifulSoup`)

## Примечание
Сайт Росстата использует JavaScript, поэтому текущая версия требует браузер (Selenium). Цель — сделать облегчённую версию без GUI.

