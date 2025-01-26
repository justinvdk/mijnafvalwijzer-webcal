#!/usr/bin/env python

import os
import re
import requests
import sys
from datetime import datetime, date, timedelta
from icalendar import Calendar, Event, Alarm

base_url = "https://www.afval3xbeter.nl"

def destruct_housenumber(housenumber):
  housenumber_suffix = ""
  housenumber_re = re.search(r"^(\d+)(\D*)$", housenumber)
  if housenumber_re.group():
    housenumber = housenumber_re.group(1)
    housenumber_suffix = housenumber_re.group(2) or ""

  return housenumber, housenumber_suffix

# https://www.afval3xbeter.nl/adressen/{postcode}:{housenumber}
def get_address_metadata(postal_code, housenumber):
  url = f'{base_url}/adressen/{postal_code}:{housenumber}'
  address_response = requests.get(url)
  address_response.raise_for_status

  return address_response.json()

# https://www.afval3xbeter.nl/rest/adressen/{bagid}/kalender/2022
def get_calendar(bagid, year):
  url = f'{base_url}/rest/adressen/{bagid}/kalender/{year}'
  calendar_response = requests.get(url)
  calendar_response.raise_for_status

  return calendar_response.json()

# https://www.afval3xbeter.nl/rest/adressen/{bagid}/afvalstromen
def get_waste_types_metadata(bagid):
  url = f'{base_url}/rest/adressen/{bagid}/afvalstromen'
  waste_types_response = requests.get(url)
  waste_types_response.raise_for_status

  # cheeky to_dict
  waste_types = {}
  for waste_type in waste_types_response.json():
    waste_types[waste_type['id']] = waste_type

  return waste_types

def make_ical(address_metadata, calendar_data):
  all_waste_types_metadata = get_waste_types_metadata(address_metadata['bagid'])

  summary_format = os.getenv("MIJNAFVALWIJZER_SUMMARY_FORMAT", "Afval - {description}")
  description_format = os.getenv("MIJNAFVALWIJZER_DESCRIPTION_FORMAT", "{description}")

  now = datetime.now()

  cal = Calendar()
  cal.add("prodid", "-//{0}//NL".format(sys.argv[0]))
  cal.add("version", "2.0")
  cal.add("name", "Afvalkalender")
  cal.add("x-wr-calname", "Afvalkalender")
  cal.add("x-wr-timezone", "Europe/Amsterdam")
  cal.add("description", address_metadata['description'])
  cal.add("url", "https://www.afval3xbeter.nl/wanneer")

  alarm = Alarm()
  alarm.add("action", "DISPLAY")
  alarm.add("description", "Kliko op straat")
  alarm.add("trigger", timedelta(-1))

  max_item_date_event = None

  for calendar_item_data in calendar_data:
    waste_type = calendar_item_data["afvalstroom_id"]

    item_date = datetime.strptime(calendar_item_data['ophaaldatum'], "%Y-%m-%d")
    item_description = all_waste_types_metadata[calendar_item_data['afvalstroom_id']]['title']

    event = Event()

    # Remember last item.
    if max_item_date_event is None or max_item_date_event["dtstart"].dt < item_date:
      max_item_date_event = event

    event.add("uid", "{0}-{1}-{2}".format(item_date.year, item_date.timetuple().tm_yday, waste_type))
    event.add("dtstamp", now)
    event.add("dtstart", item_date)
    event.add("dtend", item_date + timedelta(1))
    event.add("summary", summary_format.format(description = item_description))
    event.add("description", description_format.format(description = item_description))
    event.add_component(alarm)

    cal.add_component(event)

  # To be sure, lets not assume empty.
  if max_item_date_event is None:
    max_item_date_event = Event()
    max_item_date_event.add("uid", "nothingfound")
    max_item_date_event.add("dtstamp", now)
    max_item_date_event.add("dtstart", now)
    max_item_date_event.add("dtend", now + timedelta(1))
    max_item_date_event.add("summary", "WARNING - NO EVENTS FOUND")
    max_item_date_event.add("description", "WARNING - NO EVENTS FOUND")
    max_item_date_event.add_component(alarm)
    cal.add_component(max_item_date_event)
  else:
    # We've seen it all, lets update the description of the last seen item (chronologically).
    max_item_date_event["summary"] = f'[LAST] {max_item_date_event["summary"]}'
    max_item_date_event["description"] = f'[LAST] {max_item_date_event["description"]}'


  return cal.to_ical().decode("utf-8")

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage {0} postal_code housenumber".format(sys.argv[0]))
    exit(1)

  postal_code = sys.argv[1]
  housenumber = sys.argv[2]

  housenumber, housenumber_suffix = destruct_housenumber(housenumber)

  address_metadatas = get_address_metadata(postal_code, housenumber)
  address_metadatas = list(filter(lambda metadata: metadata['huisletter'] == housenumber_suffix, address_metadatas))

  if len(address_metadatas) != 1:
    raise f'ambiguous postal_code and housenumber combination. Found {len(address_metadatas)} matches, expecting 1.'

  address_metadata = address_metadatas[0]

  now = datetime.now()
  current_year = now.year

  calendar = []
  # Get prev. year in januari.
  if now.month == 1:
    calendar = calendar + get_calendar(address_metadata['bagid'], current_year - 1)
  # Get current year data.
  calendar = calendar + get_calendar(address_metadata['bagid'], current_year)
  # Get next year in december.
  if now.month == 12:
    calendar = calendar + get_calendar(address_metadata['bagid'], current_year + 1)

  ical = make_ical(address_metadata, calendar)

  print(ical)
