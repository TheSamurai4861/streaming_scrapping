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

    # This method allows you to obtain the title of the media to be searched on the site.
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

    # This method provides links to the films in the search.
    def search_serie(self, serie_name):
        url = "https://wiflix.promo/index.php?do=search"

        # I run the query with these headers
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
            soup = BeautifulSoup(response.text, 'html.parser')
            # I find the blocks containing the media
            serie_divs = soup.find_all('div', class_='mov-mask flex-col ps-link')
            
            serie_links = [result.get('data-link') for result in serie_divs]
            return serie_links
        return f"Error: {response.status_code}"

    # This method checks that a link corresponds to the media you're looking for.
    def verify_serie_details(self, serie_link, title, original_title, season):
        response = requests.get(serie_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            title_temp = soup.find('h1')
            if title_temp:
                title_text = unidecode(title_temp.get_text(strip=True)).lower()
                title_match = (unidecode(title).lower() in title_text or unidecode(original_title).lower() in title_text)
                season_match = re.search(f"saison {str(season)}", title_text)
                if title_match and season_match:
                    return serie_link
        return None

    # This method returns streaming links
    def get_streaming_links(self, verified_link):
        response = requests.get(verified_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            episode_divs = soup.find_all('div', class_=re.compile(r'^ep\d+vf$'))
            episodes_links = {}

            for div in episode_divs:
                episode_number = re.search(r'ep(\d+)vf', div['class'][0]).group(1)
                episode_key = f'ep{episode_number}'
                links = []

                a_with_links = div.find_all('a', href=True)
                for a in a_with_links:
                    href = a['href']
                    link = href.split('/vd.php?u=')[1]
                    links.append(link)

                if links:
                    episodes_links[episode_key] = links
            return episodes_links
        return None

    # Main method
    def find_serie_on_wiflix_by_id(self, serie_id, season):
        serie_data = self.get_serie_data_from_tmdb(serie_id)
        if serie_data:
            serie_name = serie_data["title"]
            search_results = self.search_serie(serie_name)
            for link in search_results:
                verified_link = self.verify_serie_details(link, serie_name, serie_data["original_title"], season)
                if verified_link:
                    streaming_links = self.get_streaming_links(verified_link)
                    if streaming_links:

                        return streaming_links
                    return 'No links for this serie'
        return None


if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # Media TMDb id 
    tmdb_api_key = "YOUR_TMDB_API_KEY"
    serie_id = 1396

    scraper = SerieScraper(headers, tmdb_api_key)
    serie_links = scraper.find_serie_on_wiflix_by_id(serie_id, 1)
    print(serie_links)
