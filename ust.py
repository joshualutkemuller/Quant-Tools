import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker

import bs4
import pandas as pd
import requests


    
#BASE_URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=all")
#)

def get_spreads(df):
    """Transforms existing data frame"""
    
    import pandas as pd
    
    df["10Y3M_SPREAD"] = df.apply(lambda x: x["BC_10YEAR"] - x["BC_3MONTH"], axis = 1)
    
    df["10Y2Y_SPREAD"] = df.apply(lambda x: x["BC_10YEAR"] - x["BC_2YEAR"], axis = 1)
    
    df["5Y2Y_SPREAD"] = df.apply(lambda x: x["BC_5YEAR"] - x["BC_2YEAR"], axis = 1)    

    df["10Y5Y_SPREAD"] = df.apply(lambda x: x["BC_10YEAR"] - x["BC_5YEAR"], axis = 1)    

    df["30Y5Y_SPREAD"] = df.apply(lambda x: x["BC_30YEAR"] - x["BC_5YEAR"], axis = 1)     

    df["30Y2Y_SPREAD"] = df.apply(lambda x: x["BC_30YEAR"] - x["BC_2YEAR"], axis = 1) 
    
    df["30Y3M_SPREAD"] = df.apply(lambda x: x["BC_30YEAR"] - x["BC_3MONTH"], axis = 1) 
    
    df= df[["date","10Y3M_SPREAD","10Y2Y_SPREAD","5Y2Y_SPREAD", "10Y5Y_SPREAD", "30Y5Y_SPREAD", "30Y2Y_SPREAD", "30Y3M_SPREAD"]]
    
    return df

def get_url_all():
    """Return URL for XML file that holds all data from 1990 to present.
    Currently not used, reserved for furture use.
    """
    return BASE_URL.format("all")


def get_url(year: int, BASE_URL: str) -> str:
    return BASE_URL.format(year)


def fetch(url: str):
    return requests.get(url).text


def raise_if_empty(content: str) -> str:
    if "Error" in content:
        # when calling API too often an error emerges.
        raise ValueError("Cannot read from web. Try again later.")
    else:
        return content


def get_xml_content_from_web(year: int, BASE_URL:str) -> str:
    """Safely return XML content as string"""
    url = get_url(year, BASE_URL)
    return raise_if_empty(fetch(url))


def default_folder():
    dirname = "xml"
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return dirname


def filepath(year: int, folder=None):
    if not folder:
        folder = default_folder()
    filename = "{}.xml".format(year)
    return os.path.join(folder, filename)


def read(path):
    with open(path, "r") as f:
        return f.read()


def save(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)


@dataclass
class Rates:
    year: int
    folder: str
    df_columns: list
    BASE_URL:str
    BC_KEYS: list
    

    @property
    def path(self):
        return os.path.join(self.folder, f"{self.year}.xml")

    def exists(self):
        return os.path.exists(self.path)

    def fetch_xml(self):
        return get_xml_content_from_web(self.year,self.BASE_URL)

    def save_local(self):
        content = self.fetch_xml()
        save(self.path, content)
        return self

    def column_keys(self):
        return self.BC_KEYS

    def yield_datapoints(self):
        xml_content = read(self.path)
        return yield_datapoints_from_string(xml_content, self.column_keys())

    def dataframe(self):
        return to_dataframe(self.yield_datapoints(),self.df_columns)

    def data(self):
        xml_content = read(self.path)
        soup = bs4.BeautifulSoup(xml_content, "xml")
        return soup.find_all("content")


def get_date(string) -> str:
    dt = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")
    return dt.strftime("%Y-%m-%d")


def yield_datapoints_from_string(xml_content, BC_KEYS) -> Iterable[dict]:
    """Parse XML string and yield one dictionary per date."""
    soup = bs4.BeautifulSoup(xml_content, "xml")
    data = soup.find_all("content")
    for datum in data:
        cur_dict = dict((key, elem(datum, key)) for key in BC_KEYS)
        # ignore type check with pyright below
        cur_dict["date"] = get_date(datum.find("NEW_DATE").text)  # type: ignore
        yield cur_dict


def elem(datum, key):
    # Needed to work around omissions in 30yr data starting year 2002
    # Also parsing 1990 is not like 2022
    x = datum.find(key)
    try:
        return float(x.text)
    except (ValueError, AttributeError):
        # pd.NA is not stable
        return 0


def to_dataframe(gen,df_columns):
    df = pd.DataFrame(gen)[df_columns]
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df


def concat_dataframes(dfs):
    df = pd.concat(dfs).sort_index()
    return df[(df.sum(axis=1) != 0)]


def year_now():
    from datetime import datetime

    return datetime.today().year


def available_years():
    return list(range(1990, year_now() + 1))


def check_year(year):
    if year not in available_years():
        raise ValueError(f"{year} not supported.")


def years(start_year, end_year):
    check_year(start_year)
    check_year(end_year)
    assert start_year <= end_year
    return list(range(start_year, end_year + 1))


def save_xml(year, folder,df_columns,BASE_URL, BC_KEYS, overwrite=False):
    if overwrite:
        force_save(year, folder, df_columns,BASE_URL,BC_KEYS)
    else:
        soft_save(year, folder, df_columns,BASE_URL, BC_KEYS)


def force_save(year, folder,df_columns,BASE_URL, BC_KEYS):
    r = Rates(year, folder, df_columns,BASE_URL, BC_KEYS)
    r.save_local()
    print("Updated", r.path)


def soft_save(year, folder,df_columns,BASE_URL,BC_KEYS):
    r = Rates(year, folder,df_columns,BASE_URL,BC_KEYS)
    if not r.exists():
        r.save_local()
        print("Saved data for year", year)
    else:
        print("No action taken - file already exists", r.path)


def save_rates(start_year, end_year, folder,df_columns,BASE_URL,BC_KEYS):
    for year in years(start_year, end_year):
        soft_save(year, folder,df_columns,BASE_URL,BC_KEYS)


# Used in testing to read both 1990 and 2021.
def from_years(years: list, folder: str, df_columns: list, BASE_URL:str, BC_KEYS:list):
    dfs = [get_df(year, folder, df_columns,BASE_URL,BC_KEYS) for year in years]
    return concat_dataframes(dfs)


def read_rates(start_year, end_year, folder, df_columns, BASE_URL, BC_KEYS):
    year_range = years(start_year, end_year)
    return from_years(year_range, folder, df_columns, BASE_URL, BC_KEYS)


def get_df(year, folder, df_columns, BASE_URL, BC_KEYS):
    r = Rates(year, folder, df_columns, BASE_URL, BC_KEYS)
    return r.dataframe()


def draw(folder=default_folder()):
    current_year = year_now()
    save_xml(current_year, folder, overwrite=True)
    df = read_rates(1990, current_year, folder)
    df.to_csv("ust.csv")
    make_chart(df, "ust.png")


def make_chart(df, output_file):
    import matplotlib.dates as dates
    import matplotlib.pyplot as plt
    import matplotlib.ticker as plticker

    ax = df[["BC_3MONTH", "BC_2YEAR", "BC_10YEAR"]].plot()
    #ax.xaxis.set_major_locator(base=1.0)
    ax.xaxis.set_major_locator(dates.YearLocator(1))
    ax.xaxis.set_major_formatter(dates.DateFormatter("%Y"))
    plt.tight_layout()

    plt.savefig(output_file)

def date_generator():
  """Uses the datetime package to generate number month, number year"""
  import datetime
  d = datetime.datetime.now()
  print("Today's date is: ", d)
  
  full_month = d.strftime("%B")
  full_year = d.strftime("%Y")
  number_month = d.strftime("%m")
  
  return full_month, full_year, number_month