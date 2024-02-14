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

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class AtoutFranceClient:
    def __init__(self):
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
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch': '1',
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel': 'no',
        }

        self.default = "NA"

        nb_results = self._get_number_of_results()
        self.results_per_page = self._get_number_of_results_per_page()
        self.number_of_pages = self._get_number_of_pages()
        print(
            f"We found {nb_results} results on {self.number_of_pages} pages.")
        print(f"Each page contains {self.results_per_page} results.")
        while True:
            self.user_pages = input(f"Enter the number of pages to scrape: ")
            if self.user_pages == "":
                break
            elif not self.user_pages.isdigit():
                print("Invalid input. Please enter a number.")
            elif int(self.user_pages) < 1 or int(self.user_pages) > self.number_of_pages:
                print(f"Invalid input. Please enter a number between 1 and {self.number_of_pages}.")
            else:
                self.number_of_pages = int(self.user_pages)
                break
        self._update_page_to_params()

    def _get_number_of_results(self) -> int:
        response = self._send_request()
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        nb_results = soup.select_one(
            "div.oec-links-result > div.result-value").text.strip()
        nb_results = "".join(nb_results.strip(
            "résultats correspondent à votre recherche").strip().split())
        nb_results = int(nb_results)
        return nb_results
    
    def _get_number_of_results_per_page(self) -> int:
        response = self._send_request()
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        hotel_divs = soup.find_all('div', class_='facility-detail js-facility-detail')
        return len(hotel_divs)

    def _get_number_of_pages(self) -> int:
        nb_results = self._get_number_of_results()
        nb_pages = math.ceil(nb_results / self.results_per_page)
        return nb_pages

    def _update_page_to_params(self, page: int = 1) -> None:
        self.params["_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_page"] = page

    def _send_request(self) -> requests.models.Response:
        response = requests.get(
            self.base_url, headers=self.headers, params=self.params)
        response.raise_for_status()
        return response

    def _extract_hotels_from_response(self, response: requests.models.Response) -> List[BeautifulSoup]:
        soup = BeautifulSoup(response.text, "html.parser")
        hotels = soup.select("div.facility-detail.js-facility-detail")
        datas = []
        for hotel in hotels:
            hotel_id = hotel.attrs["data-tab"]
            data = soup.select_one(hotel_id)
            datas.append(data)
        return datas

    def parse_hotel(self, hotel: BeautifulSoup) -> Dict[str, str]:
        hotel_id = hotel.attrs["id"].split("-")[-1]

        try:
            name = hotel.select_one("div.facility-detail-title > span").text.strip()
        except AttributeError:
            name = self.default

        try:
            category = hotel.select_one("div.facility-detail-lead").text.strip()
        except AttributeError:
            category = self.default

        try:
            location = hotel.select_one("i.iconq-location").parent.text.strip()
            location = re.sub("\n+", " ", location)
            location = re.sub(" +", " ", location)

            match = re.search(r"^(.*?) - (\d{5}) (.+)$", location)
            if match:
                address = match.group(1).strip()
                postal_code = match.group(2).strip()
                city = match.group(3).strip().upper()
                if "ARRONDISSEMENT" in city:
                    city = city.replace("ARRONDISSEMENT", "").strip()
            else:
                address = ""
                postal_code = ""
                city = ""

        except AttributeError:
            location = self.default
            address = ""
            postal_code = ""
            city = ""

        try:
            telephone_url = f"https://www.classement.atout-france.fr/recherche-etablissements?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilitySearch&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=%2Ffacility%2Fget-text-image&p_p_cacheability=cacheLevelPage&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_facilityId={hotel_id}&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_fieldType=phone_number&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel=no&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch=1"
            response = requests.get(telephone_url)
            image = Image.open(BytesIO(response.content))
           
            telephone = pytesseract.image_to_string(image)
            telephone = telephone.replace('"', '').replace("'", '').replace('‘', "").replace('O', '0').replace('o', '0').replace(' ', '').strip()
            # sometimes a 0 is recognized at the beginning of the number
            if len(telephone) > 10:
                telephone = telephone[1:]
        except AttributeError:
            telephone = self.default

        try:
            website = hotel.select_one("a.facility-detail-link.facility-detail-site").attrs["href"]
        except AttributeError:
            website = self.default

        try:
            email_url = f"https://www.classement.atout-france.fr/recherche-etablissements?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilitySearch&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=%2Ffacility%2Fget-text-image&p_p_cacheability=cacheLevelPage&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_facilityId={hotel_id}&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_fieldType=email&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel=no&_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch=1"
            response = requests.get(email_url)
            image = Image.open(BytesIO(response.content))

            email = pytesseract.image_to_string(image).replace('"', "").strip()
        except AttributeError:
            email = self.default

        try:
            id_ = hotel.attrs["id"]
            id_ = id_.split("-")[-1]
            url = f"https://www.classement.atout-france.fr/details-etablissement?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet&p_p_lifecycle=0&_fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet_facilityId={id_}"
        except:
            url = self.default

        try:
            etoiles = hotel.select("div.rate-wrapper > svg.svg.svg--star")
            etoiles = str(len(etoiles))
        except AttributeError:
            etoiles = self.default

        return {
            "Type": category,
            "Nom": name,
            "Étoiles": etoiles,
            "Adresse": address,
            "Code postal": postal_code,
            "Ville": city,
            "Email": email,
            "Téléphone": telephone,
            "Site de l'hôtel": website,
            "Atout France URL": url,
        }

    def scrape_all_pages(self, verbose: bool = True) -> Iterator[Dict]:
        for page in tqdm(range(1, self.number_of_pages + 1)):
            self._update_page_to_params(page)
            response = self._send_request()
            hotels = self._extract_hotels_from_response(response)

            for hotel in hotels:
                datas = self.parse_hotel(hotel)

                yield datas

    def _generate_filename(self, filetype: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        filename = f"hotels-atout-france-{timestamp}.{filetype}"
        return filename

    def download_all_datas(self, verbose: bool = True) -> None:

        # Ask the user for the file format
        while True:
            print("Select the file format:")
            print("1: CSV")
            print("2: Excel (XLSX)")
            choice = input("Enter your choice (1 or 2): ")

            if choice == "1":
                filetype = "csv"
                break
            elif choice == "2":
                filetype = "xlsx"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

        filename = self._generate_filename(filetype)
        print("File name is:", filename)
        if filetype == "csv":
            with open(filename, mode="a", encoding="utf-8") as file:
                hotels = self.scrape_all_pages(verbose)
                first_hotel = next(hotels)
                fieldnames = list(first_hotel.keys())
                csv_file = csv.DictWriter(file, fieldnames=fieldnames, lineterminator='\n')
                csv_file.writeheader()
                csv_file.writerow(first_hotel)

                for hotel in hotels:
                    csv_file.writerow(hotel)


            # Fixes the UTF-8 aberrations in the CSV file
            with open(filename, mode="r", encoding="latin1") as file:
                rows = csv.reader(file)
                fixed_rows = []

                for row in rows:
                    fixed_row = [cell.encode("latin1").decode("utf-8", errors="replace") for cell in row]
                    fixed_rows.append(fixed_row)

            with open(filename, mode="w", encoding="utf-8", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(fixed_rows)

            print(f"CSV file {filename} encoding fixed.")

        elif filetype == "xlsx":
            workbook = openpyxl.Workbook()
            worksheet = workbook.active

            hotels = self.scrape_all_pages(verbose)
            first_hotel = next(hotels)
            fieldnames = list(first_hotel.keys())
            worksheet.append(fieldnames)
            worksheet.append(list(first_hotel.values()))

            for hotel in hotels:
                worksheet.append(list(hotel.values()))

            workbook.save(filename)

            print(f"Data available in {os.path.abspath(filename)}.")

        else:
            raise ValueError("Invalid file type. Must be 'csv' or 'xlsx'.")
        
        # Fixes the UTF-8 aberrations in the CSV file        

if __name__ == "__main__":
    client = AtoutFranceClient()
    client.download_all_datas()
