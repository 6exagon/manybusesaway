'''
Constants and implementations of package interfaces for King County Metro.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface, CSS_SPECIAL

MAIN_URL = 'cdn.kingcounty.gov/-/media/king-county/depts/metro/'\
    + 'fe-apps/schedule/08302025/js/find-a-schedule-js.js'
TROLLEY_URL = 'metro.kingcounty.gov/up/rr/m-trolley.html'
ROUTE_PATTERN = re.compile(r'<option value="([^"]+)">(DART +)?([A-Z\d]+?)'\
    + r'(?: Line| Shuttle)? - (.*?)<\/option>')
SERVICE_PATTERN = re.compile(r'Service between (.*) and (?:the | )(.*)')
LINK_BASE = 'https://kingcounty.gov'
# King is the only reliable agency for route directions corresponding to
# listing order, unfortunately
LINK_OPTIONS = ('#route-map', '#weekday', '#weekday-b')

class RouteListing(RouteListingInterface):
    # This could be gotten from higher up, but this is a sanity check
    AGENCY = 'king'

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
            self.existence = 1
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
        match = SERVICE_PATTERN.match(string)
        if match:
            self.start, self.dest = match.group(1), match.group(2)
            return
        points = string.split(',')
        while (points[0].startswith('Serves') or 'School' in points[0]):
            del points[0]
        self.start = points[0].lstrip().rstrip()
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
        main_js = resources[MAIN_URL]
        if not main_js:
            return
        trolley_html = resources[TROLLEY_URL]
        if not trolley_html:
            # Not a disaster, we can just render without visible trolley colors
            trolley_html = ''
        for match in ROUTE_PATTERN.finditer(main_js):
            if match.group(2):
                number = match.group(2).rstrip() + match.group(3)
            else:
                number = match.group(3)
            rl = self.get_add_routelisting(number)
            rl.existence = 1
            rl.parse_termini(match.group(4))
            rl.set_links(LINK_BASE + match.group(1), LINK_OPTIONS)
            if 'Route ' + rl.number in trolley_html:
                rl.css_class = 'trolley'
