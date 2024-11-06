import requests
from bs4 import BeautifulSoup

# Define the URL to scrape
url = 'https://bilyonaryo.com/'  # Replace with your target URL

# Fetch the webpage content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Save the raw HTML content into a .html file
    output_filename = 'bilyon_scraped_data.html'  # Set the desired filename
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Raw HTML data has been saved to {output_filename}")
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
