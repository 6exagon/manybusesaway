'''
Constants and implementations of package interfaces for Intercity Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface
from requests import request_all

# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'www.intercitytransit.com/plan-your-trip/routes'
ROUTE_PATTERN = re.compile(
    r'id":"([^"]+)","route_long_name":"[^"]+","route_short_name":"([^"]+)"')
LINK_BASE = 'https://'
# Allows no options; navigation is all done through JavaScript
TABLE_NUM = re.compile(r'"route_short_name":"([^"]+)"}')
TABLE_URL = 'www.intercitytransit.com/ride-fetch/api/route_schedule?route_id='
TABLE_PATTERN = re.compile(
    r'"Directions":{"0":"([^"]+?)(?: via [^"]+)?","1":"([^"]+?)(?: via [^"]+)?"')

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        super().__init__()

    def parse_termini(self, resource):
        '''
        Intercity Transit routes each require a separate webpage to be loaded
        and parsed.
        '''
        match = TABLE_PATTERN.search(resource)
        if match:
            self.start = match.group(1)
            self.dest = match.group(2)
        # If unable to match, just give up

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Intercity Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        # Termini are not visible until we make this request
        timetable_requests = []
        for match in ROUTE_PATTERN.finditer(html):
            # Deal with nightline
            if match.group(2) != 'NL':
                rl = self.get_add_routelisting(match.group(2))
            else:
                rl = self.get_add_routelisting('41')
            rl.isdelisted = False
            link = MAIN_URL + '/' + match.group(2)
            rl.set_links(LINK_BASE + link)
            timetable_requests.append(TABLE_URL + match.group(1))
        timetable_resources = request_all(timetable_requests, self.verbose)
        for i, res in enumerate(timetable_resources):
            # timetable_requests are in the same order as resources
            match = TABLE_NUM.search(res)
            rl = self.routelistings[match.group(1)]
            rl.parse_termini(res)
