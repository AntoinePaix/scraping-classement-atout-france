import csv
import datetime
import math
import os
import re
from typing import Dict, Iterator, List
from tqdm import tqdm
import openpyxl
import requests
from PIL import Image
from io import BytesIO
import pytesseract
import requests
from bs4 import BeautifulSoup
import questionary
from questionary import ValidationError, Validator


class AtoutFranceGeneralClient:
    def __init__(self, page: int = 1):
        self.base_url = "https://www.classement.atout-france.fr/recherche-etablissements"
        self.headers = {
            # Firefox
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/100.0',
            'Accept': '*/*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-PJAX': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'https://www.classement.atout-france.fr/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.params = {
            'p_p_id': 'fr_atoutfrance_classementv2_portlet_facility_FacilitySearch',
            'p_p_lifecycle': '0',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch': page,
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel': 'no',
        }

    def get_number_of_results(self):
        response = requests.get(
            self.base_url, headers=self.headers, params=self.params)
        soup = BeautifulSoup(response.text, 'html.parser')
        results_div = soup.find('div', {'class': 'result-value'}).text

        # Use regex to find all digits in the string
        number_of_results = re.findall(r'\d+', results_div)

        # The findall function returns a list, so join the elements into a single string
        number_of_results = ''.join(number_of_results)
        return number_of_results

    def get_number_of_pages(self):
        response = requests.get(
            self.base_url, headers=self.headers, params=self.params)
        soup = BeautifulSoup(response.text, 'html.parser')
        pagination_div = soup.find(
            'div', {'class': 'pagination'}).find_all('a')[-2].text
        if pagination_div is None:
            return 1
        return int(pagination_div)

    def get_facility_ids(self, page: int) -> List[str]:
        self.params['p_pn'] = page
        response = requests.get(
            self.base_url, headers=self.headers, params=self.params)
        soup = BeautifulSoup(response.text, 'html.parser')
        hotels = soup.select("div.facility-detail.js-facility-detail")
        datas = []
        for hotel in hotels:
            data_tab = hotel.attrs.get("data-tab")
            hotel_id = data_tab.split("-")[1]  # Split the string at the dash and take the second part
            datas.append(hotel_id)
        return datas

    def get_all_facility_ids(self) -> List[str]:
        all_facility_ids = []
        for page in tqdm(range(1, 3)):
            all_facility_ids.extend(self.get_facility_ids(page))
        return all_facility_ids
    


class AtoutFranceFacilityClient:
    def __init__(self, facility_id: str):
        self.base_url = "https://www.classement.atout-france.fr/details-etablissement"
        self.headers = {
            # Firefox
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/100.0',
            'Accept': '*/*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-PJAX': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'https://www.classement.atout-france.fr/etablissement/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.params = {
            "p_p_id": "fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet",
            "p_p_lifecycle": 0,
            "_fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet_facilityId": facility_id,
        }


class PageNumberValidator(Validator):
    def validate(self, document):
        try:
            value = int(document.text)
        except ValueError:
            raise ValidationError(
                message="Please enter a number",
                cursor_position=len(document.text))  # Move cursor to end

        if value < 1 or value > number_of_pages:
            raise ValidationError(
                message="Please enter a number between 1 and {}".format(
                    number_of_pages),
                cursor_position=len(document.text))  # Move cursor to end

# def ask_for_info_to_collect():
#     facility_data = [
#         {
#             "question": "Do you want to collect the phone number (take long time)?",
#             "key": 'phone',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the email (take long time)?",
#             "key": 'email',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the type of property (Hotel, Camping, ...) ?",
#             "key": 'type',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the name of property?",
#             "key": 'nom',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the number of stars?",
#             "key": 'stars',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the address?",
#             "key": 'address',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the postal code?",
#             "key": 'postal_code',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the city?",
#             "key": 'city',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the website?",
#             "key": 'website',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect main information? (can be doubled with other questions)",
#             "key": 'main_info',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the Atout France URL?",
#             "key": 'af_url',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the classification date?",
#             "key": 'classification_date',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the capacity in persons?",
#             "key": 'capacity_persons',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the capacity in rooms?",
#             "key": 'capacity_rooms',
#             "value": None,
#             "collect": None
#         },
#         {
#             "question": "Do you want to collect the capacity in accommodations?",
#             "key": 'capacity_accommodations',
#             "value": None,
#             "collect": None
#         },
#         # Add similar dictionaries for the other pieces of information...
#     ]

#     try:
#         for data in facility_data:
#             question = questionary.select(
#                 data["question"], choices=['Yes', 'No'])
#             data["collect"] = question.unsafe_ask()
#     except KeyboardInterrupt:
#         print("Script execution cancelled.")
#         exit()

#     return facility_data


def ask_how_many_pages_to_scrape():
    try:
        return_all = questionary.confirm(
            "Do you want to scrape all pages?").unsafe_ask()
        if return_all:
            return number_of_pages
        else:
            return questionary.text("How many pages do you want to scrape?", validate=PageNumberValidator).unsafe_ask()
    except KeyboardInterrupt:
        print("Script execution cancelled.")
        exit()


def ask_scrape_type():
    return questionary.select(
        "What type of scrape you want?", choices=['Test', 'Fast (no contact phone or email)', 'Full (very long!)']).unsafe_ask()


def scrape_data(facility_id: int = 15187, full_scrape: bool = False):
    default_value = 'N/A'
    # Scrape the data
    facility_page = AtoutFranceFacilityClient(facility_id)
    response = requests.get(
        facility_page.base_url, headers=facility_page.headers, params=facility_page.params)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # If full scrape, get the phone and email with Tesseract OCR
    phone = default_value
    email = default_value
    if full_scrape:
        try:
            phone_url = f"https://www.classement.atout-france.fr/recherche-etablissements?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilitySearch&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=%2Ffacility%2Fget-text-image&p_p_cacheability=cacheLevelPage&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_facilityId={facility_id}&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_fieldType=phone_number&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel=no&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch=1"
            response = requests.get(phone_url)
            image = Image.open(BytesIO(response.content))
            phone = pytesseract.image_to_string(image)
            phone = phone.replace('"', '').replace("'", '').replace('‘', "").replace('O', '0').replace('o', '0').replace(' ', '').replace('l', '1').strip()
            # sometimes a 0 is recognized at the beginning of the number
            if len(phone) > 10:
                phone = phone[1:]
        except AttributeError:
            phone = default_value

        try:
            email_url = f"https://www.classement.atout-france.fr/recherche-etablissements?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilitySearch&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=%2Ffacility%2Fget-text-image&p_p_cacheability=cacheLevelPage&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_facilityId={facility_id}&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_fieldType=email&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel=no&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch=1"
            response = requests.get(email_url)
            image = Image.open(BytesIO(response.content))

            email = pytesseract.image_to_string(image).replace('"', "").strip()
        except AttributeError:
            email = default_value
    
    try:
        type = soup.select_one("div.facility-detail-lead").text.strip()
    except Exception as e:
        type = default_value
    try:
        name = soup.find(
            'h1', {'class': 'facility-detail-title'}).text.strip()
    except AttributeError:
        name = default_value
    try:
        stars = len(soup.find('div', {'class': 'facility-detail-rate'}).find_all('svg', {'class': 'svg svg--star'}))
        palace = default_value
    except AttributeError:
        stars = default_value
        
    if stars == 5:
        try:
            palace_tag = soup.find('div', {'class': 'facility-detail-logo'}).find('span', {'class': 'palace-icon'})
            if palace_tag:
                palace = True
        except AttributeError:
            palace = False

    try:
        location = soup.select_one("i.iconq-location").parent.text.strip()
        location = re.sub("\n+", " ", location)
        location = re.sub(" +", " ", location)
        match = re.search(r"^(.*?) (\d{5}) (.+)$", location)
        if match:
            address = match.group(1).strip()
            postal_code = match.group(2).strip()
            city = match.group(3).strip()
        else:
            address = default_value
            postal_code = default_value
            city = default_value
    except AttributeError:
        address = default_value
        postal_code = default_value
        city = default_value

    try:
        # Find the div with the class 'facility-detail-cell', then find the nested div with class 'wrapper-list', and get all the 'li' tags inside it
        li_tags = soup.find('div', {'class': 'facility-detail-content list information'}).find('div', {
            'class': 'facility-detail-cell'}).find('div', {'class': 'wrapper-list'}).find('ul').find_all('li')
        # Iterate over the li tags and return a text array with the text of each li tag
        main_info = [li.text.replace('\n', '').replace('\t', '') for li in li_tags]

        capacity_person = main_info[0].split(' ')[2].replace(':', '')
        capacity_accommodations = main_info[0].split(' ')[3].split(',')[1]
        accommodation_type = main_info[0].split(' ')[4].strip().capitalize()
        if accommodation_type == 'Unités':
            accommodation_type = "Unités d'habitations"
        
        try:
            open_dates = main_info[1].split('Du ')[1].strip()
            open_date = open_dates.split('au ')[0] + ' au ' + open_dates.split('au ')[1]
        except IndexError:
            open_date = default_value
                
    except AttributeError:
        main_info = default_value

    try:
        website = soup.find(
            'a', {'class': 'facility-detail-link facility-detail-site'})['href']
    except AttributeError:
        website = default_value
    
    try:
        classification_date = soup.find('div', {'class': 'facility-detail_date'}).text.split(':')[1].strip()
    except AttributeError:
        classification_date = default_value
    
    try:
        af_url = f"https://www.classement.atout-france.fr/details-etablissement?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet&p_p_lifecycle=0&_fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet_facilityId={facility_id}"
    except AttributeError:
        af_url = default_value
    return {
        "ID": facility_id,
        "Type": type,
        "Nom": name,
        "Classement": stars,
        "Palace ?": palace,
        "Adresse": address,
        "Code postal": postal_code,
        "Ville": city,
        "Site web": website,
        "Date de classification": classification_date,
        "Capacité d'accueil": capacity_person,
        "Type de logements": accommodation_type,
        "Nombre de logements": capacity_accommodations,
        "Dates d'ouverture": open_date,
        "Téléphone": phone,
        "Email": email,
        "Lien AF": af_url
    }
    

def ask_file_type():
    filetype =  questionary.select(
        "What type of file do you want to save?", choices=['CSV', 'Excel']).unsafe_ask()
    if filetype == 'CSV':
        return 'csv'
    elif filetype == 'Excel':
        return 'xlsx'

def generate_file_name(filetype: str):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    filename = f"hotels-atout-france-{timestamp}.{filetype}"
    return filename

def save_to_csv(data: List[Dict], filename: str):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return filename

def save_to_excel(data: List[Dict], filename: str):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Atout France"
    for row, facility in enumerate(data, start=1):
        for col, (key, value) in enumerate(facility.items(), start=1):
            sheet.cell(row=row, column=col, value=value)
    wb.save(filename)
    return filename

            
### MAIN ###
if __name__ == "__main__":
    # Ask user type of scrape
    main_page = AtoutFranceGeneralClient()
    number_of_results = main_page.get_number_of_results()
    number_of_pages = main_page.get_number_of_pages()
    print(f"We found {number_of_results} results on {number_of_pages} pages.")
    try:
        scrape_type = ask_scrape_type()
    except KeyboardInterrupt:
        print("User canceled, exiting.")
        exit()
    else:
        try:
            filetype = ask_file_type()
        except KeyboardInterrupt:
            print("User canceled, exiting.")
            exit()
    try:
        filename = generate_file_name(filetype)
    except KeyboardInterrupt:
        print("User canceled, exiting.")
        exit()
    
    if scrape_type == 'Test':
        results = scrape_data(15187, False)
        print(results)
    else:
        facility_ids = main_page.get_all_facility_ids()
        results = []
        if scrape_type == 'Fast (no contact phone or email)':
            for facility_id in tqdm(facility_ids):
                results.append(scrape_data(facility_id, False))
                try:
                    if filetype == 'csv':
                        save_to_csv(results, filename)
                    elif filetype == 'xlsx':
                        save_to_excel(results, filename)
                except KeyboardInterrupt:
                    print("User canceled, exiting.")
                    exit()
        elif scrape_type == 'Full (very long!)':
            for facility_id in tqdm(facility_ids):
                results.append(scrape_data(facility_id, True))
                try:
                    if filetype == 'csv':
                        save_to_csv(results, filename)
                    elif filetype == 'xlsx':
                        save_to_excel(results, filename)
                except KeyboardInterrupt:
                    print("User canceled, exiting.")
                    exit()    
    print(f"Scraped {len(results)} results.")