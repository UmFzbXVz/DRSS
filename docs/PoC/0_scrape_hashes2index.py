import requests
import os
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def fetch_all_series_data():
    base_url = "https://api.dr.dk/radio/v3/search/series?q=*"
    headers = {'x-apikey': 'dinEgenAPInøgle'}
    series_data = []
    limit = 8  # API-grænse pr. side
    offset = 0  # Start offset

    while True:
        url = f"{base_url}&limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Tjek om der er elementer i svaret
        items = data.get('items', [])
        if not items:  # Stop hvis der ikke er flere elementer at behandle
            break

        for item in items:
            podcast_url = item.get('podcastUrl')
            description = item.get('description')
            program_url = item.get('presentationUrl')
            name = item.get('title')
            series_hash = fetch_series_hash(program_url)
            
            if podcast_url:
                image_url = extract_image_from_rss(podcast_url)
                
                series_data.append({
                    "name": name,
                    "url": podcast_url,
                    "image": image_url,
                    "description": description,
                    "program_url": program_url,
                    "series_hash": series_hash
                })
        
        # Gå til næste side ved at øge offset
        offset += limit

    return series_data

def fetch_series_hash(program_url):
    try:
        response = requests.get(program_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', {'name': 'cXenseParse:drk-urn'})
            if meta_tag:
                series_hash = meta_tag['content'].split(':')[-1]
                print(f"Ekstraheret serienøgle: {series_hash}")
                return series_hash
            else:
                print(f"Der blev ikke fundet nogen serienøgle i meta-tagget for {program_url}")
                return None
        else:
            print(f"Fejl ved hentning af program-URL {program_url}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fejl ved hentning af serienøgle fra {program_url}: {e}")
        return None

def extract_image_from_rss(podcast_url):
    try:
        response = requests.get(podcast_url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            image_url = root.find(".//image/url").text
            if image_url:
                print(f"Ekstraheret billed-URL: {image_url}")
                return image_url
            else:
                print(f"Der blev ikke fundet nogen billed-URL i RSS-feedet for {podcast_url}")
                return None
        else:
            print(f"Fejl ved hentning af RSS-feed fra {podcast_url}: {response.status_code}")
            return None
    except ET.ParseError:
        print(f"Fejl ved parsing af RSS-indhold fra {podcast_url}")
        return None
    except Exception as e:
        print(f"Fejl ved ekstraktion af billede fra RSS på {podcast_url}: {e}")
        return None

# Hent alle seriedata og gem dem i en JSON-fil
all_series_data = fetch_all_series_data()
output_folder = "docs"
os.makedirs(output_folder, exist_ok=True)
output_file_path = os.path.join(output_folder, 'drlyd.json')

with open(output_file_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_series_data, json_file, indent=2, ensure_ascii=False)

print(f"Alle seriedata er gemt i: {output_file_path}")
