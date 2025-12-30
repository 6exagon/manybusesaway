'''
Constants and implementations of package interfaces for Intercity Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface
from requests import request_all

AGENCY = 'Intercity Transit'
# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'www.intercitytransit.com/plan-your-trip/routes'
ROUTE_PATTERN = re.compile(r'value="[\w\d]+">([\w\d]+) \W ([\w\d\s\/]*)<')
LINK_BASE = 'https://'
# Allows no options; navigation is all done through JavaScript
# This pattern should match twice, once for the top of the table each direction
TERMS_PATTERN = re.compile(r'<tbody>\s*<tr class="timepoint".*>\s*'\
    + r'<th.*>\s*(.*?)(?:\s\[\wb\])?\s*<\/th>')

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        # Termini are not visible until we make this request
        timetable_requests = []
        for match in ROUTE_PATTERN.finditer(html):
            rl = self.get_add_routelisting(match.group(1))
            rl.existence = 1
            link = MAIN_URL + '/' + match.group(1)
            rl.set_links(LINK_BASE + link)
            # This may or may not be used
            rl.desc = match.group(2)
            timetable_requests.append(link)
        timetable_resources = request_all(timetable_requests, self.verbose)
        for i, res in enumerate(timetable_resources):
            # timetable_requests are in the same order as resources
            rl = self.routelistings[timetable_requests[i].split('/')[-1]]
            rl.parse_termini(res)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'intercity'
        self.number = short_filename
        self.css_class = ''
        super().__init__()

    def parse_termini(self, resource):
        '''
        Intercity Transit routes each require a separate webpage to be loaded
        and parsed.
        '''
        try:
            self.dest, self.start = (
                match.group(1) for match in TERMS_PATTERN.finditer(resource))
            if self.start == 'Olympia Transit Center' and '/' not in self.desc:
                self.dest = self.desc
            if self.number in ('600', '610'):
                # Both methods of assigning these are unsatisfactory
                self.dest = 'SR 512 P&R'
        except ValueError:
            # It's alright if this assignment is impossible
            pass

    def displaynum(self):
        if self.number == 'ONE':
            return '<div class="intercity-green"><p id="intercity-one">1</p>one</div>'
        return self.number
