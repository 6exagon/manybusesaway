'''
Constants and implementations of package interfaces for Kitsap Transit.
See __init__.py for documentation.
'''

import http.client
from hashlib import sha256
import hmac
from json import loads
import pickle
import re
from datetime import datetime, timezone
from time import time
from sys import stderr

from . import DataParserInterface, RouteListingInterface, CSS_SPECIAL

AGENCY = 'Kitsap Transit'
# This isn't even everything we need
# This first resource is very out of date, but we won't rely on it much
MAIN_URL = 'kttracker.com/assets/ta/kitsaptransit/config.json'
WORKER_DRIVER_URL = 'www.kitsaptransit.com/service/workerdriver-buses/'
ROUTE_PATTERN = re.compile(
    r'(?:([\w\s]+)(?:[^\s\w\.]|\sto\s))?([\w\s\.]+?)(?:\sF\w\w\w\sFerry)?')
LINK_BASE = 'https://www.kitsaptransit.com/service'
# Allows no options; everything is listed on the pages inconsistently
# Early South and Early North should be special
SPECIAL_ROUTES = ('626', '635')

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL, WORKER_DRIVER_URL}

    def update(self, resources):
        json = resources[MAIN_URL]
        wd_html = resources[WORKER_DRIVER_URL]
        tracker_json = kitsap_request(self.verbose)
        if not json or not wd_html or not tracker_json:
            return
        tracker_list = loads(tracker_json)['bustime-response']['routes']
        link_dict = loads(json)['map.infowindow.routeScheduleMap']
        # This Worker/Driver route got removed, but not from the menus yet
        wd_html = wd_html.replace('parkwood-east', '')
        # This being absent is clearly an error; number is an educated guess
        link_dict['805'] = '/routed-buses/nollwood-dial-a-ride'

        for map in tracker_list:
            num = map['rt']
            try:
                rl = self.get_add_routelisting(num)
            except AttributeError:
                # Raised on the anomalous misprint TA027 Task on the tracker
                continue
            rl.existence = 1
            rl.start = map['rtnm']
            if num.startswith('6'):
                rl.start = ' '.join(rl.start.split()[:-1])
                rl.dest = 'Naval Base Kitsap-Bremerton'
                if rl.start == 'SK/Bangor':
                    rl.start = 'South Kitsap'
                    rl.dest = 'Naval Base Kitsap-Bangor'
                w = rl.start.replace('/', ' ').replace('-', ' ').lower().split()
                # This looks super inefficient, but it's actually probably best
                # Slicing doesn't cause it to try 3 words when there's only 1
                # Also, most of the time, this succeeds first try
                for x in range(3, 0, -1):
                    ptn = wd_html.partition(
                        '/workerdriver-buses/' + '-'.join(w[:x]))
                    if ptn[1]:
                        break
            else:
                match = ROUTE_PATTERN.fullmatch(rl.start)
                if match.group(1):
                    rl.start = match.group(1)
                    rl.dest = match.group(2)
                else:
                    # Some routes will unfortunately not have a dest, and that
                    # is fine; it would be too impossible to add one
                    # Checking individual pages would be too inconsistent
                    rl.start = match.group(2)
                ptn = wd_html.partition('/routed-buses/' + num)
            # If this part fails, that's ok; a '' link will send you to the
            # main service page
            rl.set_links(LINK_BASE + ptn[1] + ptn[2].partition('"')[0])

        for key, value in link_dict.items():
            if int(key) < 400:
                # This resource is out of date for all regular buses
                continue
            rl = self.routelistings.get(key)
            if not rl:
                rl = RouteListing(key)
                self.routelistings[key] = rl
                # Get its description from the Worker/Driver HTML,
                # all we needed here was the number
                rl.existence = 1
                rl.start = wd_html.partition(value + '">')[2].partition('<')[0]
                rl.start.rstrip()
            rl.set_links(LINK_BASE + value)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'kitsap'
        if not short_filename.isnumeric():
            raise AttributeError
        self.number = short_filename
        series = int(self.number) // 100
        if series == 1:
            series = 0
        elif series == 5:
            series = 4
        self.css_class = str(series)
        if self.number in SPECIAL_ROUTES:
            self.css_class = CSS_SPECIAL
        super().__init__()

# The following is all to fetch the kttracker listings
# Deliberately opaque
K_E = 'XIwoy4D5UxSLkvISntOvwdO5N'
H_E = 'DQnfOgtJ7eSalUJlYhbXJaYdi06TZafY'
T_E = b'\x80\x04\x95\xd5\x00\x00\x00\x00\x00\x00\x00}\x94(KOKAKNKBKfKCKxKDKkK'\
    + b'EKgKFKLKGKlKHKmKIKUKJKYKKKqKLKZKMKFKNKHKOKpKPKXKQKzKRKQKSKKKTKJKUKvKV'\
    + b'KrKWKPKXKhKYKDKZKWKaKeKbKEKcKtKdKVKeKbKfKsKgKTKhKdKiKAKjKwKkKBKlKMKmK'\
    + b'iKnKuKoKcKpKnKqKCKrKIKsKRKtKyKuKoKvKSKwKaKxKjKyKGKzu.'
HEADERS = {
    'Accept': 'application/json',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'User-Agent': 'ManyBusesAway',
    'sec-ch-ua': 'ManyBusesAway'}
U_0 = '/bustime'
U_1 = '/api/v3/gettime?requestType=gettime&unixTime=true&key=%s&format=json&xtime=%d'
U_2 = '/api/v3/getroutes?requestType=getroutes&locale=en&key=%s&format=json&xtime=%d'
V_MSG = 'HTTPS requests for kttracker.com got response %s'

def kitsap_request(verbose=False):
    '''
    Returns required kttracker listings.
    Makes and closes one http.client.HTTPSConnection.
    If a response code is not 200, prints message to stderr and returns None.
    If verbose is True, prints message to stdout.
    '''
    u = pickle.loads(T_E)
    connection = http.client.HTTPSConnection('kttracker.com')
    connection.request('GET',
        U_0 + U_1 % (K_E.translate(u), round(time() * 1000)),
        headers=HEADERS)
    resp = connection.getresponse()
    if resp.status != 200:
        print(V_MSG % resp.status, file=stderr)
        connection.close()
        return None
    jsonr = resp.read().decode('utf-8')
    ht = int(loads(jsonr)["bustime-response"]["tm"]) + 20
    dt = datetime.fromtimestamp(ht // 1000).astimezone(timezone.utc).strftime(
        '%a, %d %b %Y %H:%M:%S GMT')
    key = U_2 % (K_E.translate(u), ht) + dt
    h = hmac.new(bytes(H_E.translate(u), 'utf-8'), key.encode('utf-8'), sha256)
    newheaders = {'X-Date': dt, 'X-Request-ID': h.hexdigest()}
    connection.request('GET',
        U_0 + U_2 % (K_E.translate(u), ht),
        headers=HEADERS | newheaders)
    resp = connection.getresponse()
    if resp.status == 200:
        if verbose:
            print(V_MSG % 'OK')
        returnval = resp.read().decode('utf-8')
    else:
        print(V_MSG % resp.status, file=stderr)
        returnval = None
    connection.close()
    return returnval
