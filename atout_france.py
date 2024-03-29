from __future__ import annotations

import csv
import datetime
import math
import os
import re
from copy import copy
from typing import Iterator
from typing import TypedDict

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag
from tqdm import tqdm


class Hotel(TypedDict):
    category: str
    name: str
    stars: str
    address: str
    postal_code: str
    city: str
    email: str
    phone_number: str
    website: str
    url: str


class AtoutFranceClient:
    def __init__(self):
        self.base_url = 'https://www.classement.atout-france.fr/recherche-etablissements'  # noqa: E501
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Referer': 'https://www.classement.atout-france.fr/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            # Firefox
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',  # noqa: E501
            'X-PJAX': 'true',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.params = {  # page 1 by default
            'p_p_id': 'fr_atoutfrance_classementv2_portlet_facility_FacilitySearch',
            'p_p_lifecycle': '0',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_page': '1',
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_performSearch': '1',  # noqa: E501
            '_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_is_luxury_hotel': 'no',  # noqa: E501
        }

        self.default = 'NA'
        self.results_per_page = 16

    def _get_number_of_results(self, client: httpx.Client) -> int:
        params = self._generate_params()
        response = self._send_request(client, params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        nb_results = soup.select_one(
            'div.oec-links-result > div.result-value').string.strip()
        nb_results = ''.join(nb_results.strip(
            'résultats correspondent à votre recherche').strip().split())
        nb_results = int(nb_results)
        return nb_results

    def _get_number_of_pages(self, client: httpx.Client) -> int:
        nb_results = self._get_number_of_results(client)
        nb_pages = math.ceil(nb_results / self.results_per_page)
        return nb_pages

    def _generate_params(self, page: int = 1) -> dict[str, str]:
        params = copy(self.params)
        params['_fr_atoutfrance_classementv2_portlet_facility_FacilitySearch_page'] = str(page)  # noqa: E501
        return params

    def _send_request(
        self, client: httpx.Client, params: dict[str, str],
    ) -> httpx.Response:
        response = client.get(
            self.base_url,
            params=params,
        )
        response.raise_for_status()
        return response

    def _extract_hotels_from_response(self, response: httpx.Response) -> Iterator[Tag]:
        soup = BeautifulSoup(response.text, 'html.parser')
        hotels = soup.select('div.facility-detail.js-facility-detail')
        for hotel in hotels:
            hotel_id = hotel.attrs['data-tab']
            data = soup.select_one(hotel_id)
            yield data

    def parse_hotel(self, hotel: Tag) -> Hotel:
        try:
            name = hotel.select_one(
                'div.facility-detail-title > span').string.strip()
        except AttributeError:
            name = self.default

        try:
            category = hotel.select_one(
                'div.facility-detail-lead').string.strip()
        except AttributeError:
            category = self.default

        try:
            location = hotel.select_one(
                'i.iconq-location').parent.string.strip()
            location = re.sub('\n+', ' ', location)
            location = re.sub(' +', ' ', location)

            # divide location
            match = re.search(r"^(.*?) - (\d{5}) (.+)$", location)
            if match:
                address = match.group(1).strip()
                postal_code = match.group(2).strip()
                city = match.group(3).strip()
            else:
                address = ""
                postal_code = ""
                city = ""

        except AttributeError:
            location = self.default
            address = self.default
            postal_code = self.default
            city = self.default

        try:
            phone = hotel.find(
                'div', string='Téléphone').find_next('div').string.strip()
        except AttributeError:
            phone = self.default

        try:
            website = hotel.select_one(
                'a.facility-detail-link.facility-detail-site').attrs['href']
        except AttributeError:
            website = self.default

        try:
            email = hotel.find(
                'div', string='Adresse email').find_next('div').string.strip()
        except AttributeError:
            email = self.default

        try:
            id_ = hotel.attrs['id']
            id_ = id_.split('-')[-1]
            url = f'https://www.classement.atout-france.fr/details-etablissement?p_p_id=fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet&p_p_lifecycle=0&_fr_atoutfrance_classementv2_portlet_facility_FacilityPortlet_facilityId={id_}'  # noqa: E501
        except BaseException:
            url = self.default

        try:
            stars = hotel.select('div.rate-wrapper > svg.svg.svg--star')
            stars = str(len(stars))
        except AttributeError:
            stars = self.default

        return Hotel(
            category=category,
            name=name,
            stars=stars,
            address=address,
            postal_code=postal_code,
            city=city,
            email=email,
            phone_number=phone,
            website=website,
            url=url,
        )

    def scrape_all_pages(self) -> Iterator[Hotel]:
        with httpx.Client(headers=self.headers) as client:
            num_pages = self._get_number_of_pages(client)
            with tqdm(total=num_pages) as pbar:
                for page in range(1, num_pages + 1):
                    params = self._generate_params(page)
                    response = self._send_request(client, params)
                    for hotel in self._extract_hotels_from_response(response):
                        yield self.parse_hotel(hotel)

                    pbar.update(1)

    def _generate_filename(self) -> str:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
        return f'hotels-atout-france-{timestamp}.csv'

    def download_all_datas(self) -> None:
        filename = self._generate_filename()
        with open(filename, mode='w', encoding='utf-8') as file:
            generator_hotels = self.scrape_all_pages()
            first_hotel = next(generator_hotels)
            fieldnames = first_hotel.keys()

            csv_file = csv.DictWriter(file, fieldnames=fieldnames)
            csv_file.writeheader()
            csv_file.writerow(first_hotel)

            for hotel in generator_hotels:
                csv_file.writerow(hotel)

        print(
            f'[FILE GENERATED SUCCESSFULLY] Data available at {os.path.abspath(filename)!r}',  # noqa: E501
        )


def main() -> int:
    client = AtoutFranceClient()
    client.download_all_datas()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
