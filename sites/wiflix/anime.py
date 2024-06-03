import re
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

class AnimeScraper:
    def __init__(self, headers, tmdb_api_key):
        self.headers = headers
        self.tmdb_headers = {
            "Authorization": f"Bearer {tmdb_api_key}",
            "accept": "application/json"
        }
    
    # This method allows you to obtain the title of the media to be searched on the site.
    def get_anime_data_from_tmdb(self, anime_id):
        url = f"https://api.themoviedb.org/3/tv/{anime_id}?language=fr-FR"
        response = requests.get(url, headers=self.tmdb_headers)
        if response.status_code == 200:
            data = response.json()
            serie_data = {
                "title": data["name"],
                "original_title": data["original_name"]
            }
            return serie_data
        return None

    # This method provides links to the films in the search.
    def search_anime(self, anime_name, season):
        url = "https://french-anime.com/index.php?do=search"

        # I run the query with these headers
        data = {
            "do": "search",
            "subaction": "search",
            "search_start": 0,
            "full_search": 0,
            "result_from": 1,
            "story": anime_name,
        }

        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')  # Use response.text here
            anime_divs = soup.find_all('div', class_='mov clearfix')

            anime_links = []
            for anime in anime_divs:
                link_div = anime.find('div', class_="mov-mask flex-col ps-link")
                season_span = anime.find('span', class_="block-sai")

                if link_div and season_span:
                    season_text = unidecode(season_span.get_text(strip=True)).lower()
                    pattern = re.compile(rf'0?{season}')
                    season_match = re.search(pattern, season_text)
                    if season_match:
                        anime_link = link_div.get('data-link')
                        if anime_link:
                            anime_links.append(anime_link)

            return anime_links
        return []

    # This method checks that a link corresponds to the media you're looking for.
    def verify_anime_details(self, anime_link, title, original_title):
        response = requests.get(anime_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            title_temp = soup.find('h1')
            if title_temp:
                title_text = unidecode(title_temp.get_text(strip=True)).lower()
                title_match = (unidecode(title).lower() in title_text or unidecode(original_title).lower() in title_text)
                if title_match:
                    return anime_link
        return None

    # This method returns streaming links
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

    # Main method
    def find_anime_on_wiflix_by_id(self, anime_id, season):
        anime_data = self.get_anime_data_from_tmdb(anime_id)
        if anime_data:
            anime_name = anime_data["title"]
            search_results = self.search_anime(anime_name, season)
            for link in search_results:
                verified_link = self.verify_anime_details(link, anime_name, anime_data["original_title"])
                if verified_link:
                    streaming_links = self.get_streaming_links(verified_link)
                    if streaming_links:
                        return streaming_links
                    return 'No links for this anime'
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    tmdb_api_key = "YOUR_TMDB_API_KEY"
    anime_id = 37854

    scraper = AnimeScraper(headers, tmdb_api_key)
    anime_links = scraper.find_anime_on_wiflix_by_id(anime_id, 1)
    print(anime_links)
