
import traceback
from itertools import cycle
import bs4 as bs  # pip intsall bs4
import re
import csv
import requests  # pip intsall requests
import json
from random import randint
from time import sleep
from lxml.html import fromstring  # pip intsall lxml
from retrying import retry  # pip intsall retrying

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
    'referrer': 'https://clutch.co/directory/mobile-application-developers',
    # 'Accept': '*/*',
    # 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6',
    # 'Pragma': 'no-cache',
}
count = 0
company_data = []
with open('clutch_data.json') as json_file:
    company_data = json.load(json_file)

urls = [
    "https://clutch.co/directory/mobile-application-developers",
]


def get_proxies():
    sleep(randint(5, 10))
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0],
                              i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def retry_if_connection_error(exception):
    """ Specify an exception you need. or just True"""
    # return True
    print('EXCEPTION: ', exception)
    return True

# if exception retry with 2 second wait
@retry(retry_on_exception=retry_if_connection_error, wait_exponential_multiplier=2000, wait_exponential_max=30000)
def safe_request(url):
    proxies = get_proxies()
    proxy_pool = cycle(proxies)
    proxy = next(proxy_pool)
    return requests.get(url, proxies={
        "http": proxy, "https": proxy})


try:
    for url in urls:
        #----------------------------------------------------------------#
        pageNo = 0  # 37 <- enter your last page number here

        while True:
            queries = "sort_by=0&location%5Bcountry%5D=US"
            if pageNo == 0:
                pageUrl = str(url)+"?"+queries
            else:
                page = "?page="
                pageUrl = str(url)+page+str(pageNo)+"&"+queries

            print('Fetching data from :: ', pageUrl)

            try:
                response = safe_request(url=pageUrl)
            except Exception as ex:
                print('\n Current URL:: ', url, ', page:: ', pageNo)
                print("Error occurred: {}".format(str(ex)))
                break
            # webdata = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
            # sauce = webdata.read()
            soup = bs.BeautifulSoup(response.content, 'lxml')

            # i = 0
            directory_ul = soup.find(
                "ul", {"class": "directory-list"})
            companies = directory_ul.find_all(
                "li", {"class": "provider-row"})
            # print('here is :', companies, companies == None)

            for company in companies:
                link = company.find('a', href=re.compile(
                    "^https://clutch.co/profile"))
                try:
                    comp_url = link.get('href')
                except:
                    pass
                clutch_profile = comp_url
                name = company.find("h3", {"class": "company-name"})
                tagline = company.find("p", {"class": "tagline"})
                info_list = company.find_all('div', {"class": "list-item"})
                project_size = info_list[0]
                hourly_rate = info_list[1].text.replace(
                    '\n', '').replace('/ hr', '').split('-')
                try:
                    min_hourly_rate = hourly_rate[0].replace('>', '').strip()
                    if '<' in hourly_rate[0]:
                        max_hourly_rate = hourly_rate[0].replace(
                            '<', '').strip()
                        min_hourly_rate = '0'
                except:
                    pass

                try:
                    if not max_hourly_rate:
                        max_hourly_rate = hourly_rate[1].strip()
                except:
                    max_hourly_rate = None

                employee = info_list[2].text.replace('\n', '').split('-')
                min_employee = employee[0].strip()
                max_employee = employee[1].strip()
                location = info_list[3]
                locality = location.find('span', {"class": "locality"})
                region = location.find('span', {"class": "region"})
                website = company.find('li', {"class": "website-link"})
                services_object = company.find(
                    'div', {"class": {"carousel-inner"}})
                services_html_array = services_object.find_all(
                    'div', {"class": {"item"}})
                services = []
                for service in services_html_array:
                    service = service.text.replace('\n', '').split('%')
                    services.append(
                        {'tag': service[1].strip(), 'score': service[0].strip()})

                company_json = {
                    "name": name.text.replace('\n', '').strip(),
                    "clutch_profile": comp_url.strip(),
                    "tagline": tagline.text.replace('\n', '').strip(),
                    "min_hourly_rate": min_hourly_rate,
                    "max_hourly_rate": max_hourly_rate,
                    "min_employee": min_employee,
                    "max_employee": max_employee,
                    "location": {
                        "locality": locality.text.replace('\n', '').strip(),
                        "region": region.text.replace('\n', '').strip()
                    },
                    "webiste": website.a['href'].strip(),
                    "services": services
                }
                if company_json not in company_data:
                    company_data.append(company_json)
                    count += 1
                    print('Company number:: ', count)
            sleep(randint(20, 60))
            pageNo += 1
        break
except:
    print('\nAdded Data for ', count, ' companies.')
    with open('clutch_data.json', 'w') as outfile:
        json.dump(company_data, outfile, indent=4)

print('\n DONE')
