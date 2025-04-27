'''
Constants and implementations of package interfaces for Intercity Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface
from requests import request_all

# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'www.intercitytransit.com/plan-your-trip/routes'
ROUTE_PATTERN = re.compile(r'value="([\w\d]+)">\1.*\W ([\w\d\s\/]*)<')
# Intercity Transit allows no options; navigation is all done through JavaScript
TERMS_PATTERN = re.compile(r'Outbound Stops[\s\w\d\/<>]*?<tbody>\s*'\
    + r'<tr class=\"timepoint\">\s*<th>\s*(.*?)(?: \[\wb\])?\n[\w\W]*'\
    + r'<tr class=\"timepoint\">\s*<th>\s*(.*?)(?: \[\wb\])?\n[\w\W]*</table>')

class DataParser(DataParserInterface):
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
            if match.group(1) in self.routelistings:
                rl = self.routelistings[match.group(1)]
            else:
                rl = RouteListing(match.group(1))
                self.routelistings[match.group(1)] = rl
            rl.existence = 1
            link = MAIN_URL + '/' + match.group(1)
            rl.links = tuple('https://' + link for x in range(3))
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

    def position(self):
        if self.number.isnumeric():
            return int(self.number) * 256
        elif self.number[:-1].isnumeric():
            return int(self.number[:-1]) * 256 + ord(self.number[-1])
        else:
            return 0

    def parse_termini(self, resource):
        '''
        Intercity Transit routes each require a separate webpage to be loaded
        and parsed.
        '''
        match = TERMS_PATTERN.search(resource)
        if match:
            self.start, self.dest = match.group(1), match.group(2)
            # Catch all the Olympia start ones, and use self.desc if so (mostly)
            if self.start == 'Olympia Transit Center' and '/' not in self.desc:
                self.dest = self.desc

    def displaynum(self):
        if self.number == 'ONE':
            return '<div class="intercity-green"><p id="intercity-one">1</p>one</div>'
        return self.number
