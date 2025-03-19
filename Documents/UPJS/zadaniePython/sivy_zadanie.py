from requests_html import HTMLSession
import json
import re
from datetime import datetime


class Brochure:
    def __init__(self, brochure_element):
        self.brochure_element = brochure_element
        self.title = ""
        self.thumbnail = ""
        self.shop_name = ""
        self.valid_from = ""
        self.valid_to = ""
        self.parsed_time = ""
    
    def extract_brochure_data(self):
        # data we are looking for
        self.shop_name = self.get_shop_name()
        self.thumbnail = self.get_thumbnail()
        self.valid_from, self.valid_to = self.get_valid_dates()
        self.parsed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.title = self.get_title()
    
    def get_shop_name(self):
        # Supermarket NAME
        name_attr = self.brochure_element.find('a', first=True).attrs['title']
        match = re.search(r"Prospekt des Geschäftes (.*?),", name_attr)
        return match.group(1) if match else "Unknown"

    def get_thumbnail(self):
        # THUMBNAIL url
        img_t = self.brochure_element.find('img', first=True)
        if img_t:
            return img_t.attrs.get('data-src') or img_t.attrs.get('src', '')
        return ""

    def get_valid_dates(self):
        # Valid RANGE
        valid_range_t = self.brochure_element.find('.grid-item-content small', first=True).text.strip()
        valid_range = re.search(r"(\d{2}\.\d{2}\.\d{4}) - (\d{2}\.\d{2}\.\d{4})", valid_range_t)
        
        if valid_range:
            valid_from = valid_range.group(1)
            valid_to = valid_range.group(2)
        else:
            # If no range is found
            valid_from = valid_range_t
            valid_to = 'none'
        return valid_from, valid_to

    def get_title(self):
        # TITLE
        title_t = self.brochure_element.find('.grid-item-content', first=True).text
        return title_t


class Scraper:
    def __init__(self, category_url):
        self.base_url = "https://www.prospektmaschine.de" # manualy added
        self.category_url = category_url
        self.session = HTMLSession()
        self.sups_data = []
    
    def fetch_page(self):
        # START the page with all supermarkets
        r = self.session.get(self.category_url)
        r.html.render(sleep=1, keep_page=True, scrolldown=1)
        return r

    def get_all_brochure_urls(self, r):
        # Exctract all URLs (for each supermarket)
        sup_list = r.html.find("ul#left-category-shops", first=True)
        return [self.base_url + a.attrs['href'] for a in sup_list.find("a")]
    
    def parse_page(self, r):
        # Analyze each supermarket
        sup_urls = self.get_all_brochure_urls(r)
        
        for sup_url in sup_urls:
            self.scrape_brochure_data(sup_url) # looping through URLs
        
    def scrape_brochure_data(self, sup_url):
        # Gets all the data we are looking for for each supermarket
        sup_r = self.session.get(sup_url)
        sup_r.html.render(sleep=3, keep_page=True, scrolldown=1)
        brochure_list = sup_r.html.find('.letaky-grid', first=True)
        brochure_list = brochure_list.find('.brochure-thumb')
        print(f"Scraping: {sup_url}")

        for brochure in brochure_list:

            # Check if the brochure is old
            if 'grid-item-old' in brochure.find('.grid-item.box.blue')[0].attrs.get('class', ''):
                continue  # Skip old brochures

            # Create Brochure instance and extract data
            brochure_obj = Brochure(brochure)
            brochure_obj.extract_brochure_data()

            # Collecting the data
            self.sups_data.append({
                "title": brochure_obj.title,
                "thumbnail": brochure_obj.thumbnail,
                "shop_name": brochure_obj.shop_name,
                "valid_from": brochure_obj.valid_from,
                "valid_to": brochure_obj.valid_to,
                "parsed_time": brochure_obj.parsed_time
            })

    def save_to_json(self):
        # Saving collected data
        json_data = json.dumps(self.sups_data, indent=4)
        with open('supermarket_data.json', 'w') as f:
            f.write(json_data)


# -------------------------------------|| Main block ||-------------------------------------
if __name__ == "__main__":
    scraped_page = Scraper("https://www.prospektmaschine.de/hypermarkte/")
    html = scraped_page.fetch_page()  # Fetches the page
    scraped_page.parse_page(html)  # Parses the page and scrapes data
    scraped_page.save_to_json()  # Saves data to JSON file
    print("Dáta boli uložené do supermarket_data.json")  # confirmation message