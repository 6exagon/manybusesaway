'''
Constants and implementations of package interfaces for Lewis County Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'lewiscountytransit.org/bus-routes/'
ROUTE_PATTERN = re.compile(r'--route-color:(#\w+)"><summary>([\w ]+) - <span'\
    + r' class="route_description">(?:[\w ]+ - )?([\w ]+?)(?: Route)?<')
LINK_BASE = 'https://'
# No separate links or options

class RouteListing(RouteListingInterface):
    # This could be gotten from higher up, but this is a sanity check
    AGENCY = 'lewis'

    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        self.color = 'white'
        if 'Weekend' in self.number:
            # Not a separate route
            raise AttributeError
        super().__init__()

    def position(self):
        # Lexicographic ordering is used on website, which is desirable here
        return self.number

    def displaynum(self):
        # Inline style is probably the best here
        return '<p class="smallnum" style="color:%s">%s</p>' % (
            self.color, self.number)

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Lewis County Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        for match in ROUTE_PATTERN.finditer(html):
            try:
                rl = self.get_add_routelisting(match.group(2))
            except AttributeError:
                # Raised on weekend route
                continue
            rl.existence = 1
            # These would have to be un-capitalized if gathered from HTML
            rl.start = 'Mellen Street e-Transit Station'
            if rl.number == 'Brown East':
                rl.start = 'Morton e-Transit Station'
            rl.dest = match.group(3)
            rl.color = match.group(1)
            rl.set_links(LINK_BASE + MAIN_URL)
