import requests
import os

def fetch_series_data(category_id):
    url = f"https://api.dr.dk/radio/v2/search/series?q=*&categories=urn%3Adr%3Aradio%3Acategory%3A{category_id}"
    headers = {'x-apikey': 'DIN_EGEN_API-NØGLE'}
    series_urls = []
    
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        for item in data.get('items', []):
            podcast_url = item.get('podcastUrl')
            if podcast_url:
                saved = save_to_file(podcast_url)
        url = data.get('next')

def save_to_file(podcast_url):
    folder_name = "DR Lyd RSS"
    os.makedirs(folder_name, exist_ok=True)
    rss_file_name = f"{podcast_url.split('/')[-1]}.rss"
    rss_file_path = os.path.join(folder_name, rss_file_name)
    response = requests.get(podcast_url)
    if response.status_code == 200:
        with open(rss_file_path, 'wb') as file:
            file.write(response.content)
        return False

categories_url = "https://api.dr.dk/radio/v2/categories/"
response = requests.get(categories_url)
categories_data = response.json()

for category in categories_data:
    category_id = category['id'].split(':')[-1]
    fetch_series_data(category_id)
