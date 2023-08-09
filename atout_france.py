import csv
import datetime
import math
import os
import re
from pprint import pprint
from typing import Dict, Iterator, List

import requests
from bs4 import BeautifulSoup


class AtoutFranceClient:
    def __init__(self):
        self.base_url = "https://www.classement.atout-france.fr/recherche-etablissements"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/100.0',  # Firefox
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
        self.results_per_page = 16
        self.number_of_pages = self._get_number_of_pages()
        self._update_page_to_params()

    def _get_number_of_results(self) -> int:
        response = self._send_request()
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        nb_results = soup.select_one("div.oec-links-result > div.result-value").text.strip()
        nb_results = "".join(nb_results.strip("résultats correspondent à votre recherche").strip().split())
        nb_results = int(nb_results)
        return nb_results

    def _get_number_of_pages(self) -> int:
        nb_results = self._get_number_of_results()
        nb_pages = math.ceil(nb_results / self.results_per_page)
        return nb_pages

    def _update_page_to_params(self, page: int = 1) -> None:
        self.params["_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_page"] = page

    def _send_request(self) -> requests.models.Response:
        response = requests.get(self.base_url, headers=self.headers, params=self.params)
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
        try:
            name = hotel.select_one("div.facility-detail-title > span").text.strip()
        except AttributeError:
            name = self.default

        try:
            categorie = hotel.select_one("div.facility-detail-lead").text.strip()
        except AttributeError:
            categorie = self.default

        try:
            location = hotel.select_one("i.iconq-location").parent.text.strip()
            location = re.sub("\n+", " ", location)
            location = re.sub(" +", " ", location)
        except AttributeError:
            location = self.default

        try:
            telephone = hotel.find("div", text="Téléphone").find_next("div").text.strip()
        except AttributeError:
            telephone = self.default

        try:
            website = hotel.select_one("a.facility-detail-link.facility-detail-site").attrs["href"]
        except AttributeError:
            website = self.default

        try:
            email = hotel.find("div", text="Adresse email").find_next("div").text.strip()
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
            "Nom": name,
            "Email": email,
            "Téléphone": telephone,
            "Localisation": location,
            "Catégorie": categorie,
            "Étoiles": etoiles,
            "Site": website,
            "URL": url,
        }

    def scrape_all_pages(self, verbose: bool = True) -> Iterator[Dict]:
        for page in range(1, self.number_of_pages + 1):
            self._update_page_to_params(page)
            response = self._send_request()
            hotels = self._extract_hotels_from_response(response)
            for hotel in hotels:
                datas = self.parse_hotel(hotel)
                if verbose:
                    pprint(datas)
                    print(f"Scraping page {page}/{self.number_of_pages}")

                yield datas

    def _generate_filename(self) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        filename = f"atout-france-fr-{timestamp}.csv"
        return filename

    def download_all_datas(self, verbose: bool = True) -> None:
        filename = self._generate_filename()
        with open(filename, mode="a", encoding="utf-8") as file:
            generator_hotels = self.scrape_all_pages(verbose)
            first_hotel = next(generator_hotels)

            fieldnames = first_hotel.keys()
            csv_file = csv.DictWriter(file, fieldnames=fieldnames)
            csv_file.writeheader()
            csv_file.writerow(first_hotel)

            for hotel in generator_hotels:
                csv_file.writerow(hotel)

        print(f"Data available in {os.path.abspath(filename)}.")

    # Fixes the UTF-8 aberrations in the CSV file
    def fix_csv_encoding(filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = []
            for row in reader:
                fixed_row = [cell.encode("latin1").decode("utf-8") for cell in row]
                rows.append(fixed_row)

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows)




if __name__ == "__main__":
    client = AtoutFranceClient()
    client.download_all_datas()
