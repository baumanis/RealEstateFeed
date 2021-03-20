import sqlite3
from datetime import datetime
from Constants import CRITERIA_MAPPING as CM, DB_FILENAME
from RealEstateFeed import RealEstate
from datetime import date


def new_db(path: str):
    """
    Creates a new database for storing real estate data in 'path'.
    """
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE "Ads" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Price"	REAL,
	"Size"	REAL,
	"DistrictId"	INTEGER,
	"SeriesId"	INTEGER,
	"StreetId"	INTEGER,
	"StrNum"	INTEGER,
	"Link"	TEXT,
	"ImportDate"	TEXT,
	"TypeOfDealId"	INTEGER,
	"AmenitiesId"	INTEGER,
	"UploadDate"	TEXT,
	"Floor"	INTEGER,
	"BuildingId"	INTEGER
);
CREATE TABLE "Amenities" (
	"AmenitiesId"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT NOT NULL UNIQUE
);
CREATE TABLE "Buildings" (
	"BuildingId"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT UNIQUE
);
CREATE TABLE "Districts" (
	"DistrictId"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT UNIQUE
);
CREATE TABLE "Series" (
	"SeriesId"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT UNIQUE
);
CREATE TABLE "Streets" (
	"StreetId"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT UNIQUE
);
CREATE TABLE "TypeOfDeal" (
	"TypeOfDealId"	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	"Name"	TEXT UNIQUE
)
    """)
    conn.commit()
    conn.close()


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
    """"
    Valid search criteria:
        typeofdeal: 'buy' or 'sell';
        district;
        series;
        building;
        street;
        import_date: (start, end), format 'yyyy-mm-dd';
        upload_date: (start, end) format 'yyyy-mm-dd';
        size: any real number, requires two numbers (from, to);
        price: any real number, requires two numbers (from, to);
        floor: integer;
        amenities
    """
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
        if criteria in ["district", "series", "building", "street", "typeofdeal"]:
            sql_query += f"{CM[criteria]} = '{value}'"
        elif criteria in ["size", "price"]:
            sql_query += f"{CM[criteria]} BETWEEN {value[0]} AND {value[1]}"
        elif criteria == "floor":
            sql_query += f"{CM[criteria]} = {value}"
        elif criteria == "amenities":
            sql_query += f"{CM[criteria]} LIKE '%{value}%'"
        elif criteria in ["import_date", "upload_date"]:
            if type(value) is str:
                sql_query += f"{CM[criteria]} = '{value}'"
            elif type(value) is tuple:
                start_date = [int(i) for i in value[0].split("-")]
                start_date = date(start_date[0], start_date[1], start_date[2])
                end_date = [int(i) for i in value[1].split("-")]
                end_date = date(end_date[0], end_date[1], end_date[2])
                ordinal_nums = range(start_date.toordinal(), end_date.toordinal() + 1)
                days_in_period = [date.fromordinal(i).strftime("%Y-%m-%d") for i in ordinal_nums]
                days_in_period_str = "("
                for i in range(len(days_in_period)):
                    days_in_period_str += f"'{days_in_period[i]}'"
                    if i < len(days_in_period) - 1:
                        days_in_period_str += ", "
                    else:
                        days_in_period_str += ")"
                sql_query += f"{CM[criteria]} IN {days_in_period_str}"
        sql_query += " AND "
    sql_query = sql_query[:len(sql_query) - 5]
    connect = sqlite3.connect(DB_FILENAME)
    cursor = connect.cursor()
    cursor.execute(sql_query)
    results_table = cursor.fetchall()
    connect.close()
    return [RealEstate("Manual", price=i[4], size=i[3], street=i[1], strnum=i[2], district=i[0], series=i[5],
                       link=i[7], typeofdeal=i[6], amenities=i[9], upload_date=i[10],
                       floor=i[11], building=i[12], import_date=i[8]) for i in results_table]
