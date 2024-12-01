import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json5
import os

def extract_js_object(text, var_name):
    pattern = re.compile(rf'var {var_name}\s*=\s*({{)', re.DOTALL)
    match = pattern.search(text)
    if not match:
        return None
    start = match.start(1)
    braces = 0
    idx = start
    while idx < len(text):
        char = text[idx]
        if char == '{':
            braces += 1
        elif char == '}':
            braces -= 1
            if braces == 0:
                end = idx + 1
                return text[start:end]
        idx += 1
    return None

def main():
    url = 'https://www.learnabdominal.com/cases/ct-basecamp'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    a_tags = soup.find_all('a')
    links = []
    for a in a_tags:
        href = a.get('href')
        if href and ('www.google.com/url?' in href):
            parsed_url = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                decoded_url = urllib.parse.unquote(actual_url)
                if 'pacsbin.com' in decoded_url:
                    links.append(decoded_url)

    print(f'Found {len(links)} links to process.')

    processed_file_urls = set()

    current_directory = os.path.dirname(os.path.abspath(__file__))
    save_directory = os.path.join(current_directory, 'data')
    os.makedirs(save_directory, exist_ok=True)

    with open(os.path.join(current_directory, 'duplicates.txt'), 'a') as duplicate_log, open(os.path.join(current_directory, 'errors.txt'), 'a') as error_log:
        for idx, link in enumerate(links):
            print(f'Processing link {idx+1}/{len(links)}: {link}')
            try:
                response = requests.get(link)
                response.raise_for_status()
            except Exception as e:
                print(f'Error accessing {link}: {e}')
                error_log.write(f'Error accessing {link}: {e}\n')
                continue

            page_text = response.text
            studydata_text = extract_js_object(page_text, 'studydata')
            if studydata_text:
                try:
                    studydata = json5.loads(studydata_text)
                except Exception as e:
                    print(f'Error parsing studydata from {link}: {e}')
                    error_log.write(f'Error parsing studydata from {link}: {e}\n')
                    continue
                # Extract the instances and their URLs
                series_list = studydata.get('series', [])
                for series in series_list:
                    label = series.get('label', 'unknown_label')
                    label_clean = re.sub(r'[^\w\-]', '_', label)
                    instances = series.get('instances', [])
                    for instance in instances:
                        file_url = instance.get('url')
                        if file_url:
                            if file_url in processed_file_urls:
                                print(f'File URL {file_url} already processed.')
                                duplicate_log.write(f'Duplicate file URL found: {file_url} in link {link}\n')
                                continue
                            processed_file_urls.add(file_url)
                            original_file_name = os.path.basename(file_url)
                            file_name = f"{label_clean}_{original_file_name}"
                            file_path = os.path.join(save_directory, file_name)
                            print(f'Downloading {file_url} to {file_path}')
                            try:
                                r = requests.get(file_url)
                                r.raise_for_status()
                                with open(file_path, 'wb') as f:
                                    f.write(r.content)
                            except Exception as e:
                                print(f'Error downloading {file_url}: {e}')
                                error_log.write(f'Error downloading {file_url}: {e}\n')
            else:
                print(f'Could not find studydata in the page {link}.')
                continue

if __name__ == "__main__":
    main()