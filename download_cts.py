import requests
from bs4 import BeautifulSoup
import os
import time
import re

def get_filename_from_cd(cd):
    if not cd:
        return None
    fname = re.findall('filename="?([^";]+)"?', cd)
    if len(fname) == 0:
        return None
    return fname[0]

def download_file(url, case_title, destination_folder):
    print(f'Downloading from {url}...')
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred while downloading {case_title}: {http_err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: HTTP error during download: {http_err}\n')
        return
    except Exception as err:
        print(f'An error occurred while downloading {case_title}: {err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: Error during download: {err}\n')
            return

    # Get filename from Content-Disposition header
    filename = get_filename_from_cd(response.headers.get('content-disposition'))
    if not filename:
        print(f'No Content-Disposition header for {case_title}. Skipping download.')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: Missing Content-Disposition header. Skipped download.\n')
        return

    if os.path.exists(filename):
        print(f'File {filename} already exists, skipping download.')
        return
   
    os.makedirs(destination_folder, exist_ok=True)
    with open(os.path.join(destination_folder, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f'Download of {filename} complete.')

def process_case(case_url, case_title, destination_folder):
    print(f'\nProcessing {case_title}...')
    try:
        response = requests.get(case_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred while accessing {case_title}: {http_err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: HTTP error accessing case page: {http_err}\n')
        return
    except Exception as err:
        print(f'An error occurred while accessing {case_title}: {err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: Error accessing case page: {err}\n')
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the download link
    links = soup.find_all('a', href=True)
    download_url = None
    for link in links:
        href = link['href']
        if '.zip' in href:
            download_url = href
            break

    if download_url:
        download_file(download_url, case_title, destination_folder)
    else:
        print(f'No download link found for {case_title}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'{case_title}: No download link found.\n')

def main(destination_folder):
    base_url = 'https://www.veterinaryctmasterclass.com/cases/'
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred while accessing the main page: {http_err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'Main page: HTTP error: {http_err}\n')
        return
    except Exception as err:
        print(f'An error occurred while accessing the main page: {err}')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'Main page: Error: {err}\n')
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    case_list = soup.find('ul', {'class': 'lcp_catlist', 'id': 'lcp_instance_0'})
    if not case_list:
        print('No case list found on the page.')
        with open('errors.txt', 'a') as error_file:
            error_file.write('No case list found on the main page.\n')
        return

    case_links = case_list.find_all('a')

    for link in case_links:
        case_url = link['href']
        case_title = link.get_text()
        process_case(case_url, case_title, destination_folder)
        time.sleep(2)

if __name__ == '__main__':
    main("directory name to store zip files")


