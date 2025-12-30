'''
Constants and implementations of package interfaces for Skagit Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface
from requests import request_all

AGENCY = 'Skagit Transit'
# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'www.skagittransit.org/routes/'
# Skagit Transit's formatting all over their website is absolutely horrible and
# inconsistent, and many many exceptions and regex clauses need to be added
ROUTE_PATTERN = re.compile(r'<a href="[^"]*?(\/[^\/]+\/)"[^>]*>(\d+X?)[ \W]*'\
    + r'((?:\s?[A-Z][a-z]+\.?(?: -)?)+)(?:\s?(?:to|[\w\s\.\/]+?)\s?'\
    + r'([\w\s\.]*))?<')
LINK_BASE = 'https://www.skagittransit.org/'
LINK_OPTIONS = (
    '#maincontent',
    '#CT_PageHeading_0_hschedule',
    '#CT_PageHeading_0_hschedule')
TERMS_PATTERN = re.compile(r'<h1>Route (\d+X?).*?</h1>\s*<h2>(?:Route \d+X? )?'\
    + r'([\w&\s]+?)(?:\s?\/[\/\w&\s]*?\s?([\w&\s]+?))?(?:<|\svia)')

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL}

    def update(self, resources):
        # This function is very convoluted, but basically, if a route's termini
        # can be figured out from the main page using ROUTE_PATTERN, we use that
        # If not, we fetch that page and then use TERMS_PATTERN on it
        # There are still many exceptions
        html = resources[MAIN_URL]
        if not html:
            return
        # Termini are not visible until we make this request
        timetable_requests = []
        for match in ROUTE_PATTERN.finditer(html):
            rl = self.get_add_routelisting(match.group(2))
            rl.existence = 1
            rl.set_links(LINK_BASE + match.group(1), LINK_OPTIONS)
            if match.group(4):
                rl.start = match.group(3)
                rl.dest = match.group(4)
            elif match.group(3).endswith('Connector'):
                rl.start, rl.dest, temp = match.group(3).split()
            else:
                timetable_requests.append(
                    'www.skagittransit.org' + match.group(1))
        timetable_resources = request_all(timetable_requests, self.verbose)
        for res in timetable_resources:
            if not res:
                continue
            match = TERMS_PATTERN.search(res)
            if not match:
                continue
            rl = self.routelistings[match.group(1)]
            rl.start = match.group(2)
            if match.group(3):
                rl.dest = match.group(3)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'skagit'
        self.number = short_filename
        self.css_class = ''
        super().__init__()
