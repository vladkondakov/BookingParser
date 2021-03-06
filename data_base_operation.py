import logging  # noqa:D100
from typing import List, Tuple, Dict

from data_base_setup import DBEngine

DATABASE = DBEngine

TABLE_NAMES = ['hotels', 'coordinates', 'important_facilities',
               'neighborhood_structures', 'services_offered',
               'extended_rating', 'review_rating', 'apartaments']


def get_years_opening_hotels():
    """Get hotels registration year in booking.com."""
    dates = []
    with DATABASE.begin() as connection:
        open_dates = connection.execute("SELECT open_date FROM hotels")
        dates = open_dates.fetchall()
    years = []

    for date in dates:
        if not date[0]:
            continue

        day, month, year = date[0].split('/')
        years.append(year)
    return years


def get_hotels_coordinates() -> List[Tuple]:
    """Get the coordination of hotels like (hotel_name, latitude, longitude)."""
    coordinates = []
    with DATABASE.begin() as connection:
        open_dates = connection.execute(
            "SELECT name, latitude, longitude FROM hotels INNER JOIN coordinates "
            "on hotels.hotel_id == coordinates.hotel_id")
        coordinates = open_dates.fetchall()
    logging.info("Received all hotel coordinates.")
    return coordinates


def is_hotel_exist(name: str, city: str, open_date: str) -> bool:
    """Check if the hotel with the folowing combination of name, city, open_date exists in hotels table."""
    existing = ()
    with DATABASE.begin() as connection:
        hotel = connection.execute(f"SELECT EXISTS(SELECT * FROM hotels WHERE name == '{name}'"
                                   f"AND city == '{city}' AND open_date == '{open_date}')")
        existing = hotel.fetchone()
    if existing[0] == 1:
        logging.info('HOTEL EXIST. SKIP')
        return True
    else:
        return False


def get_hotels_rating() -> List[float]:
    """Get all hotel ratings."""
    ratings = []
    with DATABASE.begin() as connection:
        open_dates = connection.execute(
            "SELECT score FROM hotels")
        ratings = open_dates.fetchall()
    logging.info("Received hotels rating.")
    return [float(rating[0]) for rating in ratings if rating[0]]


def get_hotels_from_city(city: str) -> List:
    """Get all hotels, which location is in the folowing city."""
    with DATABASE.begin() as connection:
        result = connection.execute(
            f"SELECT name, score, city FROM hotels WHERE city like '%{city}%' AND score != ''")
        hotels_info = result.fetchall()
    logging.info(f"Received hotel name, score for {city}.")
    return hotels_info


def get_important_facilities(by_stars: bool = False) -> Dict:
    with DATABASE.begin() as connection:
        result = connection.execute(
            "SELECT important_facilities, star FROM important_facilities "
            "INNER JOIN hotels on important_facilities.hotel_id == hotels.hotel_id")
        hotels_info = result.fetchall()

    important_facilities = {}
    for important_facility in hotels_info:

        facilities, star = important_facility
        facilities = facilities.strip().split(',')

        if by_stars:
            if not star:
                star = '-'
            if star not in important_facilities:
                important_facilities[star] = {}
                important_facilities[star]['amount'] = 0

        for facility in facilities:
            facility = facility.strip().replace('\n', '')
            if 'Временно не работает' in facility:
                continue
            elif facility == '':
                continue
            if 'фитнес-центр' in facility:
                facility = 'Фитнес-центр'
            elif 'Фитнес-центр' in facility:
                facility = 'Фитнес-центр'
            elif 'Парковка' in facility:
                facility = 'Парковка'
            elif 'парковка' in facility:
                facility = 'Парковка'
            elif 'завтрак' in facility:
                facility = 'Завтрак'
            elif 'Wi-Fi' in facility:
                facility = 'Wi-Fi'
            elif 'бассейн' in facility:
                facility = 'Бассейн'

            if by_stars:
                if facility in important_facilities[star]:
                    important_facilities[star][facility] += 1
                else:
                    important_facilities[star][facility] = 1
            else:
                if facility in important_facilities:
                    important_facilities[facility] += 1
                else:
                    important_facilities[facility] = 1
        important_facilities[star]['amount'] += 1
    return important_facilities


def get_average_prices_for_city(city: str, by_stars: bool = False) -> Tuple:
    with DATABASE.begin() as connection:
        result = connection.execute(
            "SELECT name, apartaments_price, hotel_beds, star FROM hotels "
            f"INNER JOIN apartaments on hotels.hotel_id == apartaments.hotel_id WHERE city like '%{city}%'")
        hotels_info = result.fetchall()

    hotels_prices = {}
    for apart in hotels_info:
        hotel_name, price, capacity, stars = apart
        price = int(price)
        if hotel_name not in hotels_prices:
            hotels_prices[hotel_name] = {}

        if 'min_price' not in hotels_prices[hotel_name]:
            hotels_prices[hotel_name]['min_price'] = price
        elif hotels_prices[hotel_name]['min_price'] > price:
            hotels_prices[hotel_name]['min_price'] = price

        if 'max_price' not in hotels_prices[hotel_name]:
            hotels_prices[hotel_name]['max_price'] = price
        elif hotels_prices[hotel_name]['max_price'] < price:
            hotels_prices[hotel_name]['max_price'] = price

        if 'sum_price' not in hotels_prices[hotel_name]:
            hotels_prices[hotel_name]['sum_price'] = price
        else:
            hotels_prices[hotel_name]['sum_price'] += price

        if 'apartaments_count' not in hotels_prices[hotel_name]:
            hotels_prices[hotel_name]['apartaments_count'] = 1
        else:
            hotels_prices[hotel_name]['apartaments_count'] += 1
        hotels_prices[hotel_name]['star'] = 'Другие' if stars == '' else stars
        hotels_prices[hotel_name]['avg_price'] = (hotels_prices[hotel_name]['sum_price']
                                                  / hotels_prices[hotel_name]['apartaments_count'])
    if by_stars:
        stars_list = ['Другие', 1, 2, 3, 4, 5]
        prices_by_stars = {star: {} for star in stars_list}
        for star in stars_list:
            max_price = sum_prices = apartaments_count = 0
            min_price = 10000000
            for value in hotels_prices.values():
                if value['star'] == star:
                    if value['min_price'] < min_price:
                        min_price = value['min_price']
                    if value['max_price'] > max_price:
                        max_price = value['max_price']
                    apartaments_count += value['apartaments_count']
                    sum_prices += value['sum_price']
            if apartaments_count == 0:
                continue
            avg_price = round(sum_prices / apartaments_count, 2)
            minimal_percentage = "{:.2%}".format(min_price / avg_price)
            maximal_percentage = "{:.2%}".format(max_price / avg_price)
            normal_range = f'{minimal_percentage} - {maximal_percentage}'
            prices_by_stars[star]['min_price'] = min_price
            prices_by_stars[star]['avg_price'] = avg_price
            prices_by_stars[star]['max_price'] = max_price
            prices_by_stars[star]['range'] = normal_range
        return prices_by_stars
    else:
        apartaments_count = sum_prices = avg_min_price = avg_price = avg_max_price = max_price = count_hotels = 0
        min_price = 100000000
        for value in hotels_prices.values():
            count_hotels += 1
            apartaments_count += value['apartaments_count']
            sum_prices += value['sum_price']
            if value['min_price'] < min_price:
                min_price = value['min_price']
            if value['max_price'] > max_price:
                max_price = value['max_price']
            avg_min_price += value['min_price']
            avg_max_price += value['max_price']
        avg_price = round(sum_prices / apartaments_count)
        avg_min_price = round(avg_min_price / count_hotels)
        avg_max_price = round(avg_max_price / count_hotels)
        return (min_price, avg_min_price, avg_price, avg_max_price, max_price)


def remove_extra_rows() -> None:
    """Remove existing rows from all tables by name, city and open date combination."""
    with DATABASE.begin() as connection:
        repeated_hotels_id = connection.execute(
            "SELECT hotel_id, name, city, open_date "
            "FROM hotels "
            "WHERE hotel_id NOT IN (SELECT MIN(hotel_id) "
            "FROM hotels GROUP BY name, city, open_date);"
        )

        repeated_hotels = repeated_hotels_id.fetchall()
        for hotel_id, name, city, open_date in repeated_hotels:
            for table in TABLE_NAMES:
                connection.execute(f"DELETE FROM {table} WHERE hotel_id == {hotel_id}")

    logging.info(f": {len(repeated_hotels)} Extra rows removed!")
