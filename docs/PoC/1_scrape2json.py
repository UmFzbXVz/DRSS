import requests
import json
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def load_podcast_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        podcast_data = json.load(file)
    return podcast_data

def add_offset(url, offset):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['offset'] = [str(offset)]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))
    return new_url

def fetch_podcast_links(series_hash, retries=5):
    base_url = f"https://api.dr.dk/radio/v3/pages/series/urn:dr:radio:series:{series_hash}"
    headers = {'x-apikey': 'dinEgenAPInøgle'}
    links = set()
    visited_urls = set()

    def fetch_page(url):
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    attempt += 1
                    print("Afvist. Forsøger igen..")
                    time.sleep(1)
                else:
                    print(f"Fejl ved hentning af data fra URL {url}: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Fejl ved hentning af data fra URL {url}: {e}")
                return None
        return None

    url = base_url

    while url:
        if url in visited_urls:
            break
        visited_urls.add(url)

        print("Henter side:", url)
        data = fetch_page(url)
        if not data:
            break

        groups = data.get('groups', [])
        for group in groups:
            for link in (group.get('self'), group.get('next')):
                if link:
                    full_url = link if link.startswith('http') else urljoin(base_url, link)
                    links.add(full_url)

        next_url = data.get('next') or data.get('self')
        if next_url:
            full_url = next_url if next_url.startswith('http') else urljoin(base_url, next_url)
            url = full_url
        else:
            url = None

    return links

def fetch_episodes_from_links(links, retries=5):
    episodes = []
    headers = {'x-apikey': 'dinEgenAPInøgle'}

    def fetch_page(url, offset):
        url_with_offset = add_offset(url, offset)
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url_with_offset, headers=headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    attempt += 1
                    print("Afvist. Forsøger igen..")
                    time.sleep(1)
                else:
                    print(f"Fejl ved hentning af data fra URL {url_with_offset}: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Fejl ved hentning af data fra URL {url_with_offset}: {e}")
                return None
        return None

    for link in links:
        offset = 0
        while True:
            print(f"Henter side med offset {offset}: {link}")
            data = fetch_page(link, offset)
            if not data:
                break

            items = data.get('items', [])
            print(f"Side med offset {offset} har {len(items)} elementer.")
            if items:
                for item in items:
                    episode = {
                        'title': item.get('title'),
                        'description': item.get('description'),
                        'audioAssets': item.get('audioAssets', []),
                        'publishTime': item.get('publishTime'),
                        'url': item.get('presentationUrl'),
                        'duration': item.get('durationMilliseconds')
                    }
                    episodes.append(episode)

                if len(items) == 16:
                    offset += 16
                else:
                    break
            else:
                break

    return episodes

def main():
    json_file = "docs/drlyd.json"
    podcasts = load_podcast_data(json_file)

    for podcast in podcasts:
        series_hash = podcast.get('series_hash')
        if series_hash:
            links = fetch_podcast_links(series_hash)
            episodes = fetch_episodes_from_links(links)
            if 'episodes' not in podcast:
                podcast['episodes'] = episodes
            else:
                podcast['episodes'].extend(episodes)
        else:
            print(f"Ingen serie-hash fundet for podcast: {podcast.get('name')}")

    with open('drlyd.json', 'w', encoding='utf-8') as file:
        json.dump(podcasts, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
