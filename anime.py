import re
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

class SerieScraper:
    def __init__(self, headers, tmdb_api_key):
        self.headers = headers
        self.tmdb_headers = {
            "Authorization": f"Bearer {tmdb_api_key}",
            "accept": "application/json"
        }

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

    def search_serie(self, serie_name, season):
        url = "https://french-anime.com/index.php?do=search"
        data = {
            "do": "search",
            "subaction": "search",
            "search_start": 0,
            "full_search": 0,
            "result_from": 1,
            "story": serie_name,
        }

        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')  # Use response.text here
            results = soup.find_all('div', class_='mov clearfix')

            serie_links = []
            for link in results:
                result = link.find('div', class_="mov-mask flex-col ps-link")
                result1 = link.find('span', class_="block-sai")

                if result1:
                    title_text = unidecode(result1.get_text(strip=True)).lower()
                    pattern = re.compile(rf'0?{season}')
                    saison = re.search(pattern, title_text)
                    if saison:
                        serie_link = result.get('data-link')
                        if serie_link:
                            serie_links.append(serie_link)
            
            return serie_links
        return f"Error: {response.status_code}"


    def verify_serie_details(self, serie_link, title, original_title, saison):
        response = requests.get(serie_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            title_temp = soup.find('h1')
            if title_temp:
                title_text = unidecode(title_temp.get_text(strip=True)).lower()
                title_match = (unidecode(title).lower() in title_text or unidecode(original_title).lower() in title_text)
                if title_match:
                    return serie_link
        return None

    def get_streaming_links(self, verified_link):
        response = requests.get(verified_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            episode_div = soup.find('div', class_='eps')
            episodes_links = {}

            if episode_div:
                episodes_data = episode_div.get_text(strip=True)
                episodes_list = re.split(r'(\d+!)', episodes_data)[1:]  # Split and remove the first empty element

                for i in range(0, len(episodes_list), 2):
                    episode_number = episodes_list[i].replace('!', '').strip()
                    links = episodes_list[i + 1].split(',')
                    episode_key = f'ep{episode_number}'
                    episodes_links[episode_key] = links

            return episodes_links
        return None



    def find_serie_on_wiflix_by_id(self, serie_id, season):
        serie_data = self.get_serie_data_from_tmdb(serie_id)
        if serie_data:
            serie_name = serie_data["title"]
            search_results = self.search_serie(serie_name, season)
            for link in search_results:
                print(link)
                verified_link = self.verify_serie_details(link, serie_name, serie_data["original_title"], season)
                if verified_link:
                    streaming_links = self.get_streaming_links(verified_link)
                    if streaming_links:
                        return streaming_links
                    return 'No links for this serie'
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    tmdb_api_key = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjliZDI0YzhiMjYyNWUyMzk2ZTNlZjg2YTg5ZmU0YyIsInN1YiI6IjYyNDA1NjQxYzc0MGQ5MDA0N2EzNmNjMyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.A8j36wg36WwNkiDbdRrN_TE8b9YS46CcMBWy1DXiPsw"
    serie_id = 37854  # ID de la série sur TMDB

    scraper = SerieScraper(headers, tmdb_api_key)
    serie_links = scraper.find_serie_on_wiflix_by_id(serie_id, 1)
    print(serie_links)
