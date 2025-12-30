'''
Constants and implementations of package interfaces for Grays Harbor Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Grays Harbor Transit'
MAIN_URL = 'www.ghtransit.com/routes'
# Used for 20P and HarborFLEX routes not listed on main page
# But, on its own, it's not a great resource for start and dest
SECONDARY_URL = 'www.ghtransit.com/Bus-Schedules-Maps'
# Very complicated pattern due to inconsistency and the fact that we have to
# include WAVE/DASH information
ROUTE_PATTERN = re.compile(r'>(\w+)<\/span><\/h2>\s+<\/div>\s+<\/div>\s+.*?>'\
    + r'(?:\w+(?: &amp; | \/ ))?(\w[\w ]*)<(?:\/s|br)[\w\W]*?(https[^"]*)')
# This is unfortunately required for WAVE and DASH to get where they are
WAVE_DASH_PATTERN = re.compile(r'The [A-Z]+')
WAVE_DASH_SOLUTION = re.compile(r'>(\w+) circulator service')
SECONDARY_PATTERN = re.compile(r'>(\w+)(?:<\/[a-z]+>)+\s+.*?>([^<]+?)'\
    + r'(?:(?:<\/[a-z]+>)+| Dial)[\w\W]+?(https:[^"]*)')
# Allows no options; dissimilar PDFs are used

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL, SECONDARY_URL}

    def update(self, resources):
        main_html = resources[MAIN_URL]
        secondary_html = resources[SECONDARY_URL]
        if not main_html or not secondary_html:
            return
        for match in SECONDARY_PATTERN.finditer(secondary_html):
            rl = self.get_add_routelisting(match.group(1))
            rl.existence = 1
            rl.start = match.group(2)
            rl.set_links(match.group(3))
        for match in ROUTE_PATTERN.finditer(main_html):
            # If this causes a KeyError, the route is somehow in the more
            # complete secondary listing but not the main one
            rl = self.routelistings[match.group(1)]
            # This couldn't easily be derived from the site
            rl.start = 'Aberdeen'
            if rl.number == '45':
                rl.start = 'Elma'
            rl.dest = match.group(2)
            if WAVE_DASH_PATTERN.fullmatch(rl.dest):
                rl.dest = ''
                wdmatch = WAVE_DASH_SOLUTION.search(match.group(0))
                rl.start = wdmatch.group(1)
            # This second link-setting is because the first will only use the
            # M-F schedule if applicable; this one uses the link to whole PDF
            rl.set_links(match.group(3))

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'grays'
        self.number = short_filename
        self.css_class = ''
        if self.number.isnumeric() and len(self.number) == 3:
            self.css_class = 'harborflex'
        super().__init__()
