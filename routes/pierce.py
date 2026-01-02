'''
Constants and implementations of package interfaces for Pierce Transit.
See __init__.py for documentation.
'''

from json import loads
import re

from . import DataParserInterface, RouteListingInterface, TP_REQ, TP_PATTERN, CSS_SPECIAL

# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'piercetransit.org/pierce-transit-routes/'
ROUTE_PATTERN = re.compile(
    r'<a href="([^"]+)">(?:Route )?(Stream|\d+) ([^<]*)<\/a><\/div>')
# Allows no options; navigation is all done through JavaScript
# Gig Harbor Trolley should be special
SPECIAL_ROUTES = ('101',)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        if self.number in SPECIAL_ROUTES:
            self.css_class = CSS_SPECIAL
        super().__init__()

    def displaynum(self):
        if self.number.isnumeric():
            return self.number
        return '<p class="smallnum">Stream</p>'

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Pierce Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL, TP_REQ}

    def update(self, resources):
        html = resources[MAIN_URL]
        tp_json = resources[TP_REQ]
        if not html or not tp_json:
            return
        tp_lines_list = loads(tp_json)['result']['lines']
        # This stores map of string rlid to generator over destination listings
        tp_lines_dict = dict()
        for i in tp_lines_list:
            if i['agencyId'] == 'PT':
                #i['name'] doesn't work for 497
                dirs = tuple(x['signage'] for x in i['directions'])
                tp_lines_dict[dirs[0].partition(' ')[0]] = dirs

        for match in ROUTE_PATTERN.finditer(html):
            rl = self.get_add_routelisting(match.group(2))
            rl.existence = 1
            try:
                dirgen = tp_lines_dict.pop(match.group(2))
                rl.start, rl.dest = (
                    TP_PATTERN.fullmatch(s).group(1) for s in dirgen)
            except KeyError:
                # Something is in the PT HTML but not the trip planner data, probably 101
                rl.start = match.group(3)
            rl.set_links(match.group(1))
