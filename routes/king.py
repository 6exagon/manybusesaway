'''
Constants and implementations of package interfaces for King County Metro.
See __init__.py for documentation.
'''

# This file will unfortunately need updating at the next service change
# Discontinued routes are not being removed from the JSON listing, and it seems
# that even more updates will soon come to the formatting
# Trying to access the page for a discontinued route leads to an infinite loop
# There are some wrong destinations as well

from json import loads
import re

from . import DataParserInterface, RouteListingInterface, CSS_SPECIAL

MAIN_URL = 'cdn.kingcounty.gov/-/media/king-county/depts/metro/fe-apps/'\
    + 'routes/data/route_list.json'
CUT = (' (Snow shuttle)', ' Line')
TROLLEY_URL = 'metro.kingcounty.gov/up/rr/m-trolley.html'
LINK_BASE = 'https://kingcounty.gov/en/dept/metro/routes-and-service/'\
    + 'schedules-and-maps/'
# King is the only reliable agency for route directions corresponding to
# listing order, unfortunately
LINK_OPTIONS = ('#route-map', '#weekday', '#weekday-b')

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # King County Metro has many edge cases, and they're not even all here
        self.number = short_filename
        if short_filename.isnumeric():
            num = int(self.number)
            self.css_class = str(num // 100)
            if num in range(90, 100):
                self.css_class = CSS_SPECIAL
            if num >= 800:
                self.css_class = 'schools'
        elif self.number.startswith('DART'):
            # 775 must have DART palette, and so 7 is used for DART buses
            self.css_class = '7'
        elif self.number.startswith('X'):
            self.number = short_filename[1:]
            self.css_class = 'nonbus'
            self.isdelisted = False
        else:
            self.css_class = 'rapidride'
        super().__init__()

    def position(self):
        if self.number.isnumeric():
            return int(self.number)
        if self.number.startswith('DART'):
            return int(self.number.lstrip('DART'))
        return ord(self.number[0]) - 256

    def parse_termini(self, string):
        '''
        King County Metro routes require a more complex method to obtain
        route termini than a regex group.
        '''
        # The ". " replacement is needed due to route 215 listing typo
        points = string.replace(' (loop)', '').replace('. ', ', ').split(',')
        while (points[0].startswith('Serves') or 'School' in points[0]):
            del points[0]
        self.start = points[0].lstrip().rstrip()
        if self.number == '45':
            # Old destination still active; this is a quick fix
            points[-1] = 'UW Station'
        self.dest = points[-1].lstrip().rstrip()

    def displaynum(self):
        if self.number.startswith('DART'):
            return '<p class="king-dart">DART</p>' + self.number.lstrip('DART')
        return self.number

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'King County Metro'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL, TROLLEY_URL}

    def update(self, resources):
        json = resources[MAIN_URL]
        if not json:
            return
        trolley_html = resources[TROLLEY_URL]
        if not trolley_html:
            # Not a disaster, we can just render without visible trolley colors
            trolley_html = ''
        json_list = loads(json)
        commas = []
        for i in json_list:
            number = i['route_short_name']
            if ',' in number:
                commas.extend(number.split(', '))
        for i in json_list:
            number = i['route_short_name']
            for c in CUT:
                number = number.replace(c, '')
            if not number.isnumeric() and len(number) > 1:
                # Don't handle all the verbally-described ones
                continue
            if not i['in_service'] and number not in commas:
                # Don't handle discontinued routes; crucially, comma'd routes
                # should be included
                # New formatting has '118, 119' as in_service, for example,
                # but 118 and 119 aren't(?!)
                continue
            rl = self.get_add_routelisting('DART' * i['is_dart'] + number)
            rl.isdelisted = False
            rl.parse_termini(i['route_desc'])
            rl.set_links(LINK_BASE + i['route_url'], LINK_OPTIONS)
            if 'Route ' + rl.number in trolley_html:
                rl.css_class = 'trolley'
