import re
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

class MovieScraper:
    def __init__(self, headers, tmdb_api_key):
        self.headers = headers
        self.tmdb_headers = {
            "Authorization": f"Bearer {tmdb_api_key}",
            "accept": "application/json"
        }

    def get_movie_data_from_tmdb(self, movie_id):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=fr-FR"
        response = requests.get(url, headers=self.tmdb_headers)
        if response.status_code == 200:
            data = response.json()
            movie_data = {
                "title": data["title"],
                "original_title": data["original_title"]
            }
            return movie_data
        return None

    def search_movie(self, movie_name):
        url = "https://wiflix.promo/index.php?do=search"
        data = {
            "do": "search",
            "subaction": "search",
            "search_start": 0,
            "full_search": 0,
            "result_from": 1,
            "story": movie_name,
        }

        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='mov-mask flex-col ps-link')
            
            movie_links = [result.get('data-link') for result in results]
            return movie_links
        return f"Error: {response.status_code}"

    def verify_movie_details(self, movie_link, title, original_title):
        response = requests.get(movie_link, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            title_temp = soup.find('h1')
            if title_temp:
                title_text = unidecode(title_temp.get_text(strip=True)).lower()
                title_match = (unidecode(title).lower() in title_text or unidecode(original_title).lower() in title_text)
                if title_match:
                    return movie_link
        return None

    def get_streaming_links(self,verified_link):
        response = requests.get(verified_link, headers=headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            div_with_links = soup.find('div', class_="tabs-sel linkstab")
            if div_with_links:
                a_with_links = div_with_links.find_all('a', href=True)
                streaming_links = []
                for a in a_with_links:
                    href = a['href']
                    if 'voe.sx' in href:
                        voe_link = href.split('/vd.php?u=')[1]
                        streaming_links.append(voe_link)
                    elif 'uqload' in href:
                        uqload_link = href.split('/vd.php?u=')[1]
                        streaming_links.append(uqload_link)
                    elif 'd0' in href:
                        dood_link = href.split('/vd.php?u=')[1]
                        streaming_links.append(dood_link)

                return streaming_links

        return None

    def find_movie_on_wiflix_by_id(self, movie_id):
        movie_data = self.get_movie_data_from_tmdb(movie_id)
        if movie_data:
            movie_name = movie_data["title"]
            search_results = self.search_movie(movie_name)
            for link in search_results:
                verified_link = self.verify_movie_details(link, movie_name, movie_data["original_title"])
                if verified_link:
                    streaming_links = self.get_streaming_links(verified_link)
                    if streaming_links:
                        return streaming_links
                    return 'No links for this movie'
        return None

# Example usage
if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    tmdb_api_key = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjliZDI0YzhiMjYyNWUyMzk2ZTNlZjg2YTg5ZmU0YyIsInN1YiI6IjYyNDA1NjQxYzc0MGQ5MDA0N2EzNmNjMyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.A8j36wg36WwNkiDbdRrN_TE8b9YS46CcMBWy1DXiPsw"
    movie_id = 693134  # ID du film sur TMDB

    scraper = MovieScraper(headers, tmdb_api_key)
    movie_links = scraper.find_movie_on_wiflix_by_id(movie_id)
    if movie_links:
        for link in movie_links:
            print(link)
