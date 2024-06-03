import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class AnimeScraper:
    def __init__(self, tmdb_api_key, chrome_driver_path):
        self.tmdb_headers = {
            'Authorization': f'Bearer {tmdb_api_key}',
            'Content-Type': 'application/json;charset=utf-8'
        }
        self.chrome_driver_path = chrome_driver_path
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(self.chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def get_serie_data_from_tmdb(self, serie_id):
        url = f"https://api.themoviedb.org/3/tv/{serie_id}?language=fr-FR"
        response = requests.get(url, headers=self.tmdb_headers)
        if response.status_code == 200:
            data = response.json()
            serie_data = {
                "title": data["name"],
                "original_title": data["original_name"]
            }
            return serie_data
        return None

    def search_anime_title(self, title, saison):
        title = title.lower().replace(' ', '+')
        search_url = f"https://franime.fr/recherche?search={title}&type=TOUT&format=TOUT&status=TOUT&ordre=Ressemblance&themes=TOUT&algorithme=Normal&page=0"
        self.driver.get(search_url)
        
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[@data-toggle="tooltip" and @data-placement="top" and contains(@class, "group")]')))
        
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        links = soup.find_all('a', {'data-toggle': 'tooltip', 'data-placement': 'top', 'class': 'drop-shadow-xl focus:outline-none group'})

        def titles_are_equal(title1, title2):
            return title1.replace(" ", "").lower() == title2.replace(" ", "").lower()

        found_link = None

        for link in links:
            title_div = link.find('div', {'class': 'group-focus:text-pink-400 group-hover:text-[11px] group-focus:text-[11px] group-focus:transition-all group-hover:transition-all w-full truncate font-semibold mt-1 text-[15px] h-[30px]'})
            if title_div and titles_are_equal(title, title_div.text):
                found_link = f"https://franime.fr{link['href']}"
                break

        if found_link:
            print(found_link)
            season_url = found_link.replace('s=1', f's={saison}')
            print(season_url)
            self.driver.get(season_url)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div[3]/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/p')))
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            episodes_element = soup.select_one('#root > div > div > div.relative > div.select-none.cursor-default > div > div.mx-auto.flex.justify-between.flex-col.lg\\:px-5.xl\\:pl-\\[100px\\].xl\\:pr-\\[50px\\].lg\\:flex-row > div.lg\\:w-auto.w-full.px-4 > div > div.sm\\:max-h-\\[500px\\].lg\\:max-w-\\[350px\\].xl\\:max-w-\\[408px\\].mt-2 > div.flex.flex-wrap.flex-row.py-4 > div:nth-child(2) > p')
            if episodes_element:
                episodes_text = episodes_element.text
                episodes_number = int(episodes_text.split()[0])
                return episodes_number
        return None

    def find_video_link(self, title, saison, episodes):
        video_links = []
        for episode in range(1, episodes + 1):
            episode_url = f"https://franime.fr/anime/{title.replace(' ', '-').lower()}?s={saison}&ep={episode}&lang=vo"
            self.driver.get(episode_url)
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(@href, "video.sibnet.ru/shell.php?videoid=")]')))
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            video_element = soup.find('a', href=True, text=lambda x: 'video.sibnet.ru/shell.php?videoid=' in x)
            if video_element:
                video_links.append(video_element['href'])
        return video_links

    def close_driver(self):
        self.driver.quit()

# Utilisation de la classe
tmdb_api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjliZDI0YzhiMjYyNWUyMzk2ZTNlZjg2YTg5ZmU0YyIsInN1YiI6IjYyNDA1NjQxYzc0MGQ5MDA0N2EzNmNjMyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.A8j36wg36WwNkiDbdRrN_TE8b9YS46CcMBWy1DXiPsw'
chrome_driver_path = 'utils\chrome_driver\chromedriver-win64\chromedriver.exe'

scraper = AnimeScraper(tmdb_api_key, chrome_driver_path)
# Media TMDb id 
serie_id = '37854'
saison = '2'

serie_data = scraper.get_serie_data_from_tmdb(serie_id)
if serie_data:
    title = serie_data["title"]
    episodes = scraper.search_anime_title(title, saison)
    if episodes:
        video_links = scraper.find_video_link(title, saison, episodes)
        for link in video_links:
            print(link)
    else:
        print("Nombre d'épisodes introuvable.")
else:
    print("Données de la série introuvables.")

scraper.close_driver()
