import re
import csv
from os import listdir
from os.path import isfile, join

from lxml import html
import requests

# IHCRA URLs
PERIODICALS_URL = 'https://www.lib.umn.edu/ihrca/periodicals'
UMN_LIB_STUB = 'http://lib.umn.edu'


# Shorthand to create protocols
def create_lambda(group):
    return lambda r: r.group(group) if r.group(group) else ""


# Protocols for extracting column data from a re match object. Currently all protocols just return what is grabbed from
# the regular expression matcch object group.
protocols = {
    'title': create_lambda('title'),
    'alt_title': create_lambda('alt_title'),
    'place_of_publication': create_lambda('place_of_publication'),
    'frequency': create_lambda('frequency'),
    'date_range': create_lambda('date_range'),
    'microfilm': create_lambda('microfilm'),
    # TODO: Secondary languages can be altered to convert languages to their respective language codes.
    'secondary_languages': create_lambda('secondary_languages'),
    'format': lambda r: "M" if r.group('microfilm') else "P"
    # TODO: Add protocol to detect whether periodical is 'periodical' or 'newspaper'. Currently this column is manually
    # added.
}

# Periodical regular expression, default is the most consistent formatting I've found, additional formats may be
# added to include edge cases/entirely new formats
formats = {
    'default':
        ('(?P<title>[^\(]+(?= \()|[^,\(]+)( \((?P<alt_title>.+?)\))?, '
        '(?P<place_of_publication>((Ft.)|(St.)|(Mt.)|[^0-9,])+?(,[^0-9,]+?)*)\. +'
        '((?P<frequency>[^0-9]+?)((: )|\.))?((?P<date_range>[^\(]+?)\.)?'
        '( *\((?P<microfilm>Microfilm: .+?)\)\.)?( *(?P<secondary_languages>.+?)\.)?')
}

## CODE TO TEST A SINGLE PERIODICAL STRING ##

# test = "Informatsina Sluzhba, UKR. Biuleten' (Informational Service for the Ukrainian Christian Movement. Bulletin)," \
#        " New York, NY. 1967."
# m = re.search(formats['default'], test)
# for group in re_dict:
#     print(m.group(group))
# exit(0)

## CODE TO TEST A SINGLE PERIODICAL STRING ##


# Takes a row of text assumed to be of a single periodical as well as a format from the formats dict, returns an
# array representing a single csv row entry corresponding to the inputted periodical text
def create_entry(text, format):
    entry = re.search(format, text)
    csv_entry = []
    for column in protocols.keys():
        csv_entry.append(protocols[column](entry))
    return csv_entry


# Generates a csv containing all periodical on the page and places in ../csv/ folder for each language found in the
# lib.umn.edu website.
# Note: Not fully functional due to the inconsistent html formatting of the periodicals on the webpages
def from_website():
    main_page = requests.get(PERIODICALS_URL)
    main_doc = html.fromstring(main_page.content)

    # Grabs all the sidebar elements under 'Periodical' on the periodicals webpage
    for language_element in main_doc.xpath('//span[contains(@class, "submenu")]//a[contains(@href, "/ihrca/periodicals/")]'):
        language_page = requests.get(UMN_LIB_STUB + language_element.attrib['href'])
        langauge_doc = html.fromstring(language_page.content)
        # I tried to grab all div's with strong text here, here's where the inconsistent html formatting of the
        # different pages caused a problem for me. Some pages had text in p tags, some didn't have bold, etc.
        # This is the biggest issue with generating csv's directly from the website. I made a band-aid solution by
        # copying all the important text contents of each periodical webpage into the ../raw_text/ folder, since
        # Ellen mentioned that the code is just to convert web content into csv's, and that maintainability of code
        # was not a priority. The working solution is the from_text() function below.
        periodicals = langauge_doc.xpath('//div[contains(@class, "field-items")]//strong')
        with open("../csv/" + language_element.attrib['title'].replace('/', '-') + ".csv", 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for periodical in periodicals:
                try:
                    writer.writerow(create_entry(periodical.text + periodical.tail, formats['default']))
                except:
                    print(language_element.attrib['title'], end="")
                    try:
                        print(": " + periodical.text + periodical.tail)
                    except:
                        print()


# Generates a csv for each .txt in the ../raw_text/ folder and puts them in the ../csv/ folder.
# Note: This function correctly works on all periodicals except ~20, all of which this function will print out for
# manual addition. from_text() works off of manually created .txt's from the lib.umn.edu website, which are found in
# the ../raw_text/ folder.
def from_text():
    csv_files = [f for f in listdir("../csv/") if isfile(join("../csv/", f))]
    for csv_file in csv_files:
        periodicals = []
        with open(f"../raw_text/{csv_file}.txt", 'r') as f:
            periodicals = re.split("\n+", f.read())
        with open(f"../csv/{csv_file}", 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for periodical in periodicals:
                try:
                    writer.writerow(create_entry(periodical, formats['default']))
                except:
                    if periodical not in ["", " ", "Return to Top", "Return to top.", "Return to Top.",
                                          "Newspapers", "Serials", "Yugoslav", "Macedonia"]:
                        print(csv_file + ": " + periodical)


print()
# from_website()
# from_text()
