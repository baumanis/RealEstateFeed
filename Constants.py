RE_SELL = 0
RE_RENT = 1
HTML_PATH = [2, 2, 5, 1, 1, 0, 0, 1, 1, 0, 0, 1, 4]
RE_SIZE = 5
RE_PRICE = 8
RE_STREET = 3
RE_SERIES = 7
ELEMENTS_POST = {
    "Description": {"Tag": "div", "id": "msg_div_msg"},
    "City": {"Tag": "td", "id": "tdo_20"},
    "District": {"Tag": "td", "id": "tdo_856"},
    "Street": {"Tag": "td", "id": "tdo_11"},
    "Rooms": {"Tag": "td", "id": "tdo_1"},
    "Size": {"Tag": "td", "id": "tdo_3"},
    "Floor": {"Tag": "td", "id": "tdo_4"},
    "Series": {"Tag": "td", "id": "tdo_6"},
    "Building": {"Tag": "td", "id": "tdo_2"},
    "Amenities": {"Tag": "td", "id": "tdo_1734"},
    "Price": {"Tag": "td", "id": "tdo_8"}
}

TYPE_OF_DEAL = {"Izīrē": (RE_RENT, "rent"), "Pārdod": (RE_SELL, "sell")}
URL_RENT = "https://www.ss.lv/lv/real-estate/flats/riga/all/hand_over/"
URL_SELL = "https://www.ss.lv/lv/real-estate/flats/riga/all/sell/"
URL_BASE = "https://www.ss.lv"
CRITERIA_MAPPING = {
    "price": "Ads.Price",
    "size": "Ads.Size",
    "street": "Streets.Name",
    "strnum": "Ads.StrNum",
    "district": "Districts.Name",
    "series": "Series.Name",
    "link": "Ads.Link",
    "import_date": "Ads.ImportDate",
    "typeofdeal": "TypeOfDeal.Name",
    "amenities": "Amenities.Name",
    "upload_date": "Ads.UploadDate",
    "floor": "Ads.Floor",
    "building": "Buildings.Name"
}
DB_FILENAME = "REDB_v2.sqlite"
