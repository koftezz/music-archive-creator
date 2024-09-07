import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def get_genre_from_google_search(song_title):
    # Set up Selenium WebDriver for Safari
    driver = webdriver.Safari()  # No need to specify a Service for Safari

    try:
        # Search for the song title on Google with "Beatport" appended
        search_url = f"https://www.google.com/search?q={song_title.replace(' ', '+')}+Beatport"
        driver.get(search_url)
        print(f"Searching for: {search_url}")
        # Wait for the page to load
        time.sleep(2)  # Adjust sleep time as necessary

        # Click the first search result link
        search_results = driver.find_elements(By.CSS_SELECTOR, 'h3')
        for result in search_results:
            if 'beatport.com' in result.find_element(By.XPATH, '..').get_attribute('href').lower():
                result.click()
                break
        else:
            # If no Beatport result found, click the second result
            if len(search_results) > 1:
                search_results[1].click()
            else:
                print("No suitable search results found.")

        # Wait for the Beatport page to load
        time.sleep(2)  # Adjust sleep time as necessary

        # Parse the Beatport page
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all genre divs
        genre_divs = soup.find_all('div', class_='TrackMeta-style__MetaItem-sc-9c332570-0 hpiTYE')
        genres = []

        for genre_div in genre_divs:
            genre_tag = genre_div.find('a')  # Find the <a> tag within each genre div
            if genre_tag:
                genres.append(genre_tag.text.strip())  # Append the genre to the list

        return genres if genres else ["Unknown"]  # Return the list of genres or "Unknown" if none found
    finally:
        driver.quit()  # Close the browser

def organize_songs_by_genre(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.mp3'):
            # Clean the song title
            song_title = filename.replace('myfreemp3.vip', '').replace('.mp3', '').strip()
            # remove & from song_title
            song_title = song_title.replace('&', ' ')
            # Get genres for the song
            genres = get_genre_from_google_search(song_title)
            genres = genres[0]
            print(f"Song: {song_title}, Genres: {genres}")
            # Create genre folder if it doesn't exist
            # remove / from genres
            genres = genres.replace('/', '')
            genre_folder = os.path.join(folder_path, genres)
            if not os.path.exists(genre_folder):
                os.makedirs(genre_folder)

            # Move the file to the genre folder
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(genre_folder, filename)
            shutil.move(old_file_path, new_file_path)
            print(f'Moved: {old_file_path} to {new_file_path}')

if __name__ == "__main__":
    folder_path = "/Users/batuhanorgan/Desktop/ozu/music/music"  # Update this path
    organize_songs_by_genre(folder_path)