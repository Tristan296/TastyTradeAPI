from datetime import datetime
from datetime import date, time
from tastytrade.utils import today_in_new_york
from typing import Optional
import holidays
import pytz


def get_tasty_daily() -> date:
    """
    Gets the 0DTE expiration date for the current day.
    :return: returns the 0DTE expiration date to check against.
    """
    return(today_in_new_york())

def market_is_open():
    """
    Checks whether the U.S. stock market (NYSE) is currently open based on Eastern Standard Time (EST).
    This function considers both the current date and time, taking into account:
    - U.S. holidays observed by NYSE.
    - Weekends (Saturday and Sunday) when the market is closed.
    - Market open hours (9:00 AM to 4:00 PM EST) on weekdays when the market is open.
    """

    try:
        # Set the timezone to Eastern Standard Time (EST)
        eastern_tz = pytz.timezone('US/Eastern')
        current_time_eastern = datetime.now(eastern_tz)

        nyse_holidays = holidays.NYSE()
        today_date_str = current_time_eastern.strftime('%Y-%m-%d')
        is_holiday = nyse_holidays.get(today_date_str)
        if is_holiday:
            return False

        # Check if the current day (EST) is a weekday
        day_of_week = current_time_eastern.weekday()
        if day_of_week == 5 or day_of_week == 6:
            return False

        # Define the market open and close times in EST
        market_open_time = time(9, 0)  # Market opens at 9:00 AM EST
        market_close_time = time(16, 0)  # Market closes at 4:00 PM EST

        if market_open_time <= current_time_eastern.time() <= market_close_time:
            return True
        else:
            return False

    except Exception as err:
        print(err)

    return True