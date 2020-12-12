import sqlite3
from datetime import datetime
from Constants import CRITERIA_MAPPING as CM, DB_FILENAME
# from tkinter import messagebox as mbox


def update_static_data(source: list):
    """
    Update DB with new static elements such as streets, districts etc if any.
    """
    connect = sqlite3.connect("REDB_v2.sqlite")
    cursor = connect.cursor()
    districts = []
    streets = []
    series = []
    amenities = []
    building_types = []
    for realestate in source:
        if realestate.street not in streets:
            streets.append(realestate.street)
        if realestate.series not in series:
            series.append(realestate.series)
        if realestate.building not in building_types:
            building_types.append(realestate.building)
        if realestate.district not in districts:
            districts.append(realestate.district)
        if realestate.amenities not in amenities:
            amenities.append(realestate.amenities)
    for item in streets:
        try:
            cursor.execute("INSERT INTO Streets (Name) VALUES ('" + item + "')")
        except sqlite3.IntegrityError:
            pass
    for item in districts:
        try:
            cursor.execute("INSERT INTO Districts (Name) VALUES ('" + item + "')")
        except sqlite3.IntegrityError:
            pass
    for item in series:
        try:
            cursor.execute("INSERT INTO Series (Name) VALUES ('" + item + "')")
        except sqlite3.IntegrityError:
            pass
    for item in amenities:
        try:
            cursor.execute("INSERT INTO Amenities (Name) VALUES ('" + item + "')")
        except sqlite3.IntegrityError:
            pass
    for item in building_types:
        try:
            cursor.execute("INSERT INTO Buildings (Name) VALUES ('" + item + "')")
        except sqlite3.IntegrityError:
            pass
    connect.commit()
    connect.close()


def update_records(source: list):
    """Update database with new apartments for sale/rent."""
    connect = sqlite3.connect(DB_FILENAME)
    cursor = connect.cursor()
    for realestate in source:
        sql_command = "INSERT INTO Ads (Price, Size, StreetId, StrNum, DistrictId, SeriesId, Link, ImportDate, TypeOfDealId, AmenitiesId, UploadDate, Floor, BuildingId) VALUES ("
        sql_command += str(realestate.price) + ", "
        sql_command += str(realestate.size) + ", "
        cursor.execute("SELECT StreetId FROM Streets WHERE Name='" + realestate.street + "'")
        sql_command += str(cursor.fetchone()[0]) + ", "
        sql_command += "'" + str(realestate.strnum) + "', "
        cursor.execute("SELECT DistrictId FROM Districts WHERE Name='" + realestate.district + "'")
        sql_command += str(cursor.fetchone()[0]) + ", "
        cursor.execute("SELECT SeriesId FROM Series WHERE Name='" + realestate.series + "'")
        sql_command += str(cursor.fetchone()[0]) + ", "
        sql_command += "'" + realestate.link + "', "
        sql_command += "'" + realestate.import_date + "', "
        # cursor.execute("SELECT id FROM TypeOfDeal WHERE Name='" + realestate.typeofdeal + "'")
        sql_command += str("1, ") if realestate.typeofdeal == "rent" else str("0, ")
        cursor.execute("SELECT AmenitiesId FROM Amenities WHERE Name='" + realestate.amenities + "'")
        sql_command += str(cursor.fetchone()[0]) + ", "
        sql_command += "'" + realestate.upload_date + "', "
        sql_command += str(realestate.floor) + ", "
        cursor.execute("SELECT BuildingId FROM Buildings WHERE Name='" + realestate.building + "'")
        sql_command += str(cursor.fetchone()[0])
        sql_command += ")"
        try:
            cursor.execute(sql_command)
        except sqlite3.Error as sqlError:
            with open(f"ErrorLog_{str(datetime.now())[:10].replace('-', '')}.txt", "w+") as ErrLog:
                ErrLog.write(f"Bad SQL command: {sql_command}\n{str(sqlError)}")
            return -1
    connect.commit()
    connect.close()
    return 0


def search_by_criteria(**kwargs):
    sql_query = """
    SELECT Districts.Name, Streets.Name, Ads.StrNum, Ads.Size,
    Ads.Price, Series.Name, TypeOfDeal.Name, Ads.Link, Ads.ImportDate, Amenities.Name, Ads.UploadDate, Ads.Floor, Buildings.Name
    FROM Ads INNER JOIN Districts, Streets, TypeOfDeal, Series, Amenities, Buildings ON Ads.DistrictId = Districts.DistrictId
    AND Ads.StreetId = Streets.StreetId AND Ads.SeriesId = Series.SeriesId AND Ads.AmenitiesId = Amenities.AmenitiesId AND Ads.BuildingId = Buildings.BuildingId
    AND Ads.TypeOfDealId = TypeOfDeal.TypeOfDealId
    """
    if len(kwargs) > 0:
        sql_query += " WHERE "
    for criteria, value in kwargs.items():
        if criteria in ["district", "series", "building", "street", "typeofdeal", "import_date", "upload_date"]:
            sql_query += f"{CM[criteria]} = '{value}'"
        elif criteria in ["size", "price"]:
            sql_query += f"{CM[criteria]} BETWEEN {value[0]} AND {value[1]}"
        elif criteria == "floor":
            sql_query += f"{CM[criteria]} = {value}"
        elif criteria == "amenities":
            sql_query += f"{CM[criteria]} LIKE '%{value}%'"
        sql_query += " AND "
    sql_query = sql_query[:len(sql_query) - 5]
    print(sql_query)
    connect = sqlite3.connect(DB_FILENAME)
    cursor = connect.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    connect.close()
    return results
