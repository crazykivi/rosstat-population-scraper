from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# Настройка Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless') # Запуск на фоне
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-insecure-localhost')
options.add_argument('--log-level=3')  # Подавление INFO/WARNING логов
options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Отключение DevTools логов

driver = webdriver.Chrome(options=options)
url = 'https://rosstat.gov.ru/scripts/db_inet2/passport/munr.aspx?base=munst04'

try:
    driver.get(url)
    
    print("\nУкажите имя файла для сохранения результата")
    output_file_base = input("Введите имя файла (например, выгрузка) — будет сохранено как выгрузка_год.xlsx: ").strip()
    
    if not output_file_base:
        output_file_base = 'выгрузка'
        
    print(f"Формат файла: {output_file_base}_год.xlsx\n")

    # Ожидание загрузки районов
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "title"))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    district_divs = soup.find_all('div', class_='title', id=True)
    districts = []
    for d in district_divs:
        if d['id'].startswith('title_'):
            district_id = d['id'].replace('title_', 'a')
            name = d.get_text(strip=True)
            districts.append({'id': district_id, 'name': name})

    print("\nРайоны, доступные для обработки:")
    for i, district in enumerate(districts):
        print(f"{i + 1}. {district['name']}")

    selected_indices = input("\nВведите номера районов для исключения (через запятую, диапазон разрешён): \nПример: 1, 3-5, 7\n")
    selected_ids = set()

    if selected_indices.strip():
        try:
            parts = [x.strip() for x in selected_indices.split(',')]
            total = len(districts)
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    start = max(1, start)
                    end = min(total, end)
                    selected_ids.update(range(start - 1, end))
                else:
                    num = int(part) - 1
                    if 0 <= num < total:
                        selected_ids.add(num)
        except Exception as e:
            print("Ошибка ввода:", e)

    district_ids = [d['id'] for i, d in enumerate(districts) if i not in selected_ids]
    print("\n✅ Обрабатываются следующие районы:")
    for idx in range(len(districts)):
        if idx not in selected_ids:
            print(f"- {districts[idx]['name']}")

    # --- Выбор годов ---
    print("\n📅 Укажите годы для обработки")
    print("Пример: 2022, 2023-2025 или просто нажмите Enter для выбора текущего года")
    year_input = input("Введите диапазоны годов: ").strip()

    current_year = 2024
    years = []

    if not year_input:
        years = [current_year]
        print(f"\nВыбран текущий год: {current_year}")
    else:
        try:
            parts = [x.strip() for x in year_input.split(',')]
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    years.extend(range(start, end + 1))
                else:
                    years.append(int(part))
            years = sorted(set(years))
        except Exception as e:
            print("Ошибка ввода годов:", e)
            years = [current_year]

    print(f"\n📅 Будут обработаны годы: {', '.join(map(str, years))}")

    # --- Маппинг год -> ID checkbox'а ---
    year_map = {
        2020: 'yearlist_15',
        2021: 'yearlist_16',
        2022: 'yearlist_17',
        2023: 'yearlist_18',
        2024: 'yearlist_19',
        2025: 'yearlist_20',
    }

    base_url = ' https://rosstat.gov.ru/scripts/db_inet2/passport/'

    for year in years:
        print(f"\n🔄 Начинаем сбор данных за {year} год...\n")
        data = []

        checkbox_id = year_map.get(year)
        if not checkbox_id:
            print(f"Checkbox для года {year} не найден.")
            continue

        for district_id in district_ids:
            try:
                title_elem = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, district_id.replace('a', 'title_')))
                )
                title_elem.click()
                time.sleep(1)

                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                district_div = soup.find('div', id=district_id)

                if district_div:
                    links = district_div.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        settlement_name = link.get_text(strip=True)
                        full_url = base_url + href.strip()
                        print(f"Открываем: {full_url}")

                        driver.execute_script(f"window.open('{full_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[1])

                        try:
                            year_checkbox = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.ID, checkbox_id))
                            )
                            year_checkbox.click()

                            show_button = driver.find_element(By.ID, 'Button_Table')
                            show_button.click()

                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'god'))
                            )

                            table_html = driver.page_source
                            table_soup = BeautifulSoup(table_html, 'html.parser')

                            row = table_soup.find('td', class_='prizn', text='на 1 января')
                            if row:
                                population = row.find_next('td', class_='god').text.strip()
                                data.append({
                                    'Населенный пункт': settlement_name,
                                    f'Численность населения ({year})': population
                                })
                        except Exception as e_inner:
                            print(f"Ошибка при обработке данных ({settlement_name}, {year}): {e_inner}")
                        finally:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
            except Exception as e_outer:
                print(f"Ошибка при работе с районом {district_id} ({year}): {e_outer}")

        df = pd.DataFrame(data)
        filename = f"{output_file_base}_{year}.xlsx"
        if not df.empty:
            df.to_excel(filename, index=False)
            print(f"\n✅ Данные за {year} успешно сохранены в '{filename}'")
        else:
            print(f"\n⚠️ Нет данных для сохранения за {year}.")

finally:
    driver.quit()