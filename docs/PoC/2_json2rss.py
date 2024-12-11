import json
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime

ITUNES_NAMESPACE = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace('itunes', ITUNES_NAMESPACE)

def datetime_to_rfc822(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')

def milliseconds_to_hms(ms):
    total_seconds = ms // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def generate_rss(podcast_data):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    title = ET.SubElement(channel, "title")
    title.text = podcast_data['name']
    link = ET.SubElement(channel, "link")
    link.text = podcast_data['program_url']
    description = ET.SubElement(channel, "description")
    description.text = podcast_data['description']
    image = ET.SubElement(channel, "{%s}image" % ITUNES_NAMESPACE)
    image.set("href", podcast_data['image'])

    existing_guids = set()

    for episode in podcast_data.get('episodes', []):
        episode_guid = episode.get('url')
        if not isinstance(episode_guid, str):
            print("Fejl: Episode GUID er ikke en streng:", episode_guid)
            continue

        if episode_guid in existing_guids:
            continue

        item = ET.SubElement(channel, "item")
        episode_title = ET.SubElement(item, "title")
        episode_title.text = episode['title']
        episode_description = ET.SubElement(item, "description")
        episode_description.text = episode['description'].strip() if episode.get('description') else '(ingen beskrivelse)'

        try:
            episode_duration = ET.SubElement(item, "duration")
            episode_duration.text = milliseconds_to_hms(int(episode['duration']))
        except ValueError:
            print("Fejl ved konvertering af varighed til heltal:", episode['duration'])

        try:
            pub_date = ET.SubElement(item, "pubDate")
            pub_date.text = datetime_to_rfc822(datetime.strptime(episode['publishTime'], '%Y-%m-%dT%H:%M:%S%z')).strip()
        except ValueError:
            print("Fejl ved parsing af publishTime:", episode['publishTime'])

        guid = ET.SubElement(item, "guid")
        guid.text = episode_guid
        guid.set("isPermaLink", "false")

        try:
            enclosure = ET.SubElement(item, "enclosure")
            hb_mp3 = None
            hb_hls = None
            hb = 0

            for asset in episode['audioAssets']:
                if not isinstance(asset, dict):
                    print("Fejl: Asset er ikke et ordbogsobjekt:", asset)
                    continue

                # Tjek for den højeste bitrate MP3 asset
                if asset.get('format') == 'mp3' and asset.get('bitrate', 0) > hb:
                    hb = asset['bitrate']
                    hb_mp3 = asset

                # Hvis MP3 ikke er tilgængelig, kig efter en HLS mulighed
                if asset.get('format') == 'HLS' and hb_mp3 is None:
                    hb_hls = asset

            # Brug MP3 hvis tilgængelig, ellers falder tilbage på HLS
            if hb_mp3:
                enclosure.set("url", hb_mp3['url'])
                enclosure.set("length", str(hb_mp3.get('fileSize', 0)))
                enclosure.set("type", "audio/mpeg")
            elif hb_hls:
                enclosure.set("url", hb_hls['url'])
                enclosure.set("length", str(hb_hls.get('fileSize', 0)))
                enclosure.set("type", "audio/x-m4a")  # MIME type for HLS
            else:
                print("Ingen passende lydasset fundet for episode:", episode['title'])

        except KeyError as e:
            print(f"Fejl ved adgang til nøgle i asset: {e}")

        existing_guids.add(episode_guid)

    rss_content = ET.tostring(rss, encoding='utf-8')
    return xml.dom.minidom.parseString(rss_content).toprettyxml(indent="  ")



def generate_rss_files(data_file):
    folder_name = "RSS"
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(data_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for podcast in data:
                rss_filename = f"{folder_name}/{podcast['program_url'].rsplit('/', 1)[-1]}.rss"
                rss_content = generate_rss(podcast)
                with open(rss_filename, 'w', encoding='utf-8') as rss_file:
                    rss_file.write(rss_content)
                print(f"RSS-fil '{rss_filename}' genereret med succes.")
    except FileNotFoundError:
        print("Datafilen blev ikke fundet.")
    except Exception as e:
        print(f"En fejl opstod: {str(e)}")

if __name__ == "__main__":
    data_file = "drlyd.json"
    generate_rss_files(data_file)
