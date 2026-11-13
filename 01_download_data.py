# step 1: download the NOAA storm events files, one per year
import re
import urllib.request

import config

URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"

config.RAW_DIR.mkdir(parents=True, exist_ok=True)

# file names end with the date NOAA made them, so I read the page
# and look the name up for each year
page = urllib.request.urlopen(URL).read().decode("utf-8")

for year in range(config.FIRST_YEAR, config.LAST_YEAR + 1):
    pattern = rf"StormEvents_details-ftp_v1\.0_d{year}_c\d+\.csv\.gz"
    found = re.findall(pattern, page)

    if not found:
        print(year, "no file found on the page, check the website by hand")
        continue

    name = found[-1]   # last one if there are two versions
    target = config.RAW_DIR / name

    if target.exists():
        print(year, "already downloaded")
    else:
        print(year, "downloading", name)
        urllib.request.urlretrieve(URL + name, target)

print("Done. Files are in", config.RAW_DIR)
