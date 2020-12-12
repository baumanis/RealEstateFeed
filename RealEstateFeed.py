from bs4 import BeautifulSoup
from Constants import ELEMENTS_POST as EP, TYPE_OF_DEAL as TOD, RE_SELL, RE_RENT, URL_RENT, URL_SELL, URL_BASE
import urllib.request
from datetime import datetime
import re
import threading


def address(street: str):
    """
    Takes a street address and divides it into two parts - street name and
    number.
    """
    try:
        return [re.findall("(.+) [0-9]+", street)[0], re.findall(".+ ([0-9]+)", street)[0]]
    except IndexError:
        return [re.findall("(.+) .+", street)[0], "NA"]


def reformat_date(d: str):
    """
    Reformat date from DD.MM.YYYY to YYYY-MM-DD
    """
    return f"{d.split('.')[2]}-{d.split('.')[1]}-{d.split('.')[0]}"


class RealEstate:
    """
    Stores data about an apartment.
    """
    def __init__(self, method: str, **kwargs):
        """
        method:
            'FromLink': must contain keyword argument 'link' which is SS.lv URL.
            'Manual': all fields about apartment enetered manually. Keyword
            arguments expected: price (float), size (float), street (str),
            strnum (str), district (str), series (str),
            link (str), typeofdeal (str value 'rent' or 'sell'),
            amenities (str), upload_date (str), import_date (str), floor (int),
            building (str)
        """
        self.import_date = str(datetime.now())[:10]
        if method == "FromLink":
            self.link = kwargs["link"]
            soup = BeautifulSoup(urllib.request.urlopen(self.link).read(), "html.parser")
            self.typeofdeal = TOD[soup.find_all(name="h2", attrs={"class": "headtitle"})[0].get_text().split("/")[-1].strip()][1]
            self.price = self.pricetag(soup.find_all(name=EP["Price"]["Tag"], attrs={"id": EP["Price"]["id"]})[0].get_text())
            self.size = float(soup.find_all(name=EP["Size"]["Tag"], attrs={"id": EP["Size"]["id"]})[0].get_text().split("m")[0].replace(" ", ""))
            self.series = soup.find_all(name=EP["Series"]["Tag"], attrs={"id": EP["Series"]["id"]})[0].get_text()
            self.district = soup.find_all(name=EP["District"]["Tag"], attrs={"id": EP["District"]["id"]})[0].get_text()
            self.street = address(soup.find_all(name=EP["Street"]["Tag"], attrs={"id": EP["Street"]["id"]})[0].get_text().replace(" [Karte]", ""))[0]
            self.strnum = address(soup.find_all(name=EP["Street"]["Tag"], attrs={"id": EP["Street"]["id"]})[0].get_text().replace(" [Karte]", ""))[1]
            try:
                self.amenities = soup.find_all(name=EP["Amenities"]["Tag"], attrs={"id": EP["Amenities"]["id"]})[0].get_text()
            except IndexError:
                self.amenities = "NA"
            self.upload_date = reformat_date(soup.find_all(name="td", attrs={"class": "msg_footer", "align": "right"})[0].get_text()[8:18])
            self.floor = int(soup.find_all(name=EP["Floor"]["Tag"], attrs={"id": EP["Floor"]["id"]})[0].get_text().split("/")[0])
            try:
                self.building = soup.find_all(name=EP["Building"]["Tag"], attrs={"id": EP["Building"]["id"]})[0].get_text()
            except IndexError:
                self.building = "NA"
        elif method == "Manual":
            self.price = kwargs["price"]
            self.size = kwargs["size"]
            self.street = kwargs["street"]
            self.strnum = kwargs["strnum"]
            self.district = kwargs["district"]
            self.series = kwargs["series"]
            self.link = kwargs["link"]
            self.typeofdeal = kwargs["typeofdeal"]
            self.amenities = kwargs["amenities"]
            self.upload_date = kwargs["upload_date"]
            self.floor = kwargs["floor"]
            self.building = kwargs["building"]

    def per_sqm(self):
        """
        Calculates price per square meter.
        """
        return round(self.price / self.size, 5)

    def pricetag(self, price_des: str):
        """
        Extracts the exact price from price description, e.g. '50 000 €'
        and returns as an integer value.
        """
        if self.typeofdeal == "rent":
            if "€/mēn." not in price_des:
                raise ValueError("Invalid pricetag for typeofdeal RE_RENT. Tag '€/mēn.' not found.")
            return float(price_des.split("€/mēn.")[0].strip().replace(" ", ""))
        elif self.typeofdeal == "sell":
            return float(price_des.split("€")[0].strip().replace(" ", ""))


def find_all_rows(bs: BeautifulSoup):
    """
    bs: BeautifulSoup object containing table with apartments
    https://www.ss.lv/lv/real-estate/flats/riga/all/hand_over/pageXX.html
    return value: tuple containing id attribute for all relevant <tr> tags.
            Each id points to an apartment posting.
    """
    plain_text = bs.prettify(encoding="utf-8")
    return re.findall("tr_[0-9]+", str(plain_text))


def get_links(typeofdeal: int):
    """
    Gathers all available links for:
        typeofdeal 0: apartments for sale, 1: apartments for rent
    """
    if typeofdeal not in [RE_SELL, RE_RENT]: return -1
    base_url = URL_RENT if typeofdeal == RE_RENT else URL_SELL
    return_list = []
    page = 1
    end_of_data = False
    while not end_of_data:
        # print(f"Collecting links from page {page}...")
        current_url = f"{base_url}page{str(page)}.html" if page != 1 else base_url
        table_soup = BeautifulSoup(urllib.request.urlopen(current_url), "html.parser")
        rows = find_all_rows(table_soup)
        for row in rows:
            # print(list(table_soup.find_all(name='tr', attrs={'id': row})[0].children)[-1].get_text())
            if typeofdeal == RE_RENT and '€/mēn.' not in list(table_soup.find_all(name='tr', attrs={'id': row})[0].children)[-1].get_text():
                continue
            return_list.append(f"{URL_BASE}{table_soup.find_all(name='tr', attrs={'id': row})[0].find_all(name='a')[0]['href']}")
        next_page = table_soup.find_all(name="a", attrs={"class": "navi"})[-1]["href"]
        try:
            page = int(re.findall("page([0-9]+)\.html", next_page)[0])
        except IndexError:
            end_of_data = True
    return return_list


def get_data(links: list, re_list: list, **kwargs):
    """"
    Takes a list of links and creates RealEstate objects.
    links: a list containing links to specific post in SS.
    re_list: a list that will hold the RealEstate objects created by this method.
    **kwargs: optional arguments for updating the status of current data import in real time. Use either both or none
    of the arguments below.
        total: total number of links to be processed
        status_info: a dictionary containing key 'ImportProgress'
    """
    try:
        update_status = True if "total" in kwargs and "status_info" in kwargs and "ImportProgress" in kwargs["status_info"] else False
    except KeyError as keyerror:
        print(keyerror)
        update_status = False
    for url in links:
        try:
            re_list.append(RealEstate("FromLink", link=url))
        except ValueError:
            continue
        if update_status:
            kwargs["status_info"]["ImportProgress"] = round(len(re_list)/kwargs["total"]*100, 2)
            # print(f"Progress: {str(kwargs['status_info']['ImportProgress'])}, {str(len(re_list))} / {str(kwargs['total'])}")


def get_data_quickly(typeofdeal: int, threads: int, **kwargs):
    """"
    A threaded version of get_data which equally distributes all SS links among the number of threads specified.
    typeofdeal: 0 (sell) or 1 (rent)
    threads: number of threads to distribute the workload
    **kwargs: optional arguments for updating the status of current data import in real time.
        status_info: a dictionary containing key 'ImportProgress'
        return_list: an existing list outside of this method to store RealEstate objects
    """
    update_status = True if "status_info" in kwargs else False
    return_list = []
    thread_list = []
    all_links = get_links(typeofdeal)
    links_per_thread = len(all_links) // threads
    remainder = len(all_links) % threads
    for t in range(threads):
        end_pos = links_per_thread * (t + 1)
        if t + 1 == threads:
            end_pos += remainder
        if update_status:
            thread_list.append(threading.Thread(target=get_data, args=(all_links[links_per_thread * t:end_pos], return_list), kwargs={"status_info": kwargs["status_info"], "total": len(all_links)}))
        else:
            thread_list.append(threading.Thread(target=get_data, args=(all_links[links_per_thread * t:end_pos], return_list)))
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()
    if "return_list" in kwargs:
        kwargs["return_list"] = return_list
    else:
        return return_list


def export_to_txt(source: list, filename: str):
    """
    Export source list of RealEstate objects to a text file.
    """
    with open(f"{filename}.txt", "w+", encoding="utf-8") as OutputFile:
        OutputFile.write("Price\tSize\tStreet\tStrNum\tDistrict\tSeries\tLink\tImportDate\tTypeOfDeal\tAmenities\tUploadDate\tFloor\tBuilding\n")
        for i in source:
            OutputFile.write(f"{str(i.price)}\t{str(i.size)}\t{str(i.street)}\t{str(i.strnum)}\t{str(i.district)}\t{str(i.series)}\t{str(i.link)}\t{str(i.import_date)}\t{str(i.typeofdeal)}\t{str(i.amenities)}\t{str(i.upload_date)}\t{str(i.floor)}\t{str(i.building)}\n")


def import_from_txt(filename: str):
    """
    Creates a list of RealEstate objects from a text file.
    Text file should be tab delimited and should contain the following header:
    Price\tSize\tStreet\tStrNum\tDistrict\tSeries\tLink\tImportDate\tTypeOfDeal\tAmenities\tUploadDate\tFloor\tBuilding\n
    """
    return_list = []
    with open(f"{filename}.txt", "r", encoding="utf-8") as SourceFile:
        source_list = SourceFile.read().split("\n")
        for i in range(1, len(source_list)-1):
            split_line = source_list[i].split("\t")
            return_list.append(RealEstate("Manual", price=split_line[0], size=split_line[1], street=split_line[2], strnum=split_line[3], district=split_line[4], series=split_line[5], link=split_line[6], typeofdeal=split_line[8], amenities=split_line[9], upload_date=split_line[10], floor=split_line[11], building=split_line[12]))
    return return_list
