'''
ManyBusesAway v3.2.0
This program is used to generate an HTML file to display completed buses.
Unfortunately, an HTML file with embedded JavaScript will not work for this;
file modification dates for photographs (lost when uploading to webhosting or
GitHub) are needed to render the page.
See project README.md for more details.
'''

import os
import re
from urllib import request
import json
from datetime import datetime
from time import time
import argparse

TIME_FORMAT = '%-m/%-d/%y %-H:%M'

# Current King County Metro URL, may be subject to change in the future
KCM_URL = 'https://cdn.kingcounty.gov/-/media/king-county/depts/metro/'\
    + 'fe-apps/schedule/09142024/js/find-a-schedule-js.js'\
    + '?rev=b74ceeb7db85476cb2f92719c10e956f'
TROLLEY_URL = 'https://metro.kingcounty.gov/up/rr/m-trolley.html'
# This Sound Transit page's formatting is absolutely horrible and inconsistent,
# but it's seemingly the best resource there is
ST_URL = 'https://www.soundtransit.org/ride-with-us/schedules-maps'
# This is used for Pierce Transit and Everett Transit routes
# Though it could be, it is not used for other agencies
# This is because it's less accurate and well-maintained as a source for them
TRIPPLANNER_URL = 'https://tripplanner.kingcounty.gov/TI_FixedRoute_Line'
# These next two links are also used, purely for the schedule links
# They are inadequate for route descriptions
ET_URL = 'https://everetttransit.org/101/Schedules'
PT_URL = 'https://piercetransit.org/pierce-transit-routes'
CT_URL = 'https://www.communitytransit.org/maps-and-schedules/'\
    + 'maps-and-schedules-by-route'

KCM_PATTERN = r'<option value="([^"]+)">((?:DART +)?[A-Z\d]+?)'\
    + r'(?: Line| Shuttle)? - (.*?)<\/option>'
ST_PATTERN = r'<a href="[^"]*?([^"\/]+)"[^>]*>(?:Link |Sounder )?'\
    + r'(\d+|.)(?: Line)?.\(([^\)]*)\)'
TRIPPLANNER_PATTERN = r'.*(?:[Tt]o|-) (.*?)(?: via .*)?'
ET_PATTERN = r'<a href="([^"]+)".*>Route (\d+)<\/span><\/a>'
PT_PATTERN = r'<a href="([^"]+)">(?:Route )?(Stream|\d+)[^<]*<\/a><\/div>'
CT_PATTERN = r'"route_id":"(\d+)","route_name":"([^"]*)","route_short_name"'

KCM_LINK_BASE = 'https://kingcounty.gov%s#%s'
# Only reliable agency for directions corresponding to table, unfortunately
KCM_LINK_OPTIONS = ('route-map', 'weekday', 'weekday-b')
ST_LINK_BASE = 'https://www.soundtransit.org/ride-with-us/routes-schedules/%s%s'
ST_LINK_OPTIONS = ('', '?direction=1', '?direction=0')
ET_LINK_BASE = '%s#page=%s'
ET_LINK_OPTIONS = ('1', '2', '2')
# PT allows no options; navigation is all done through JavaScript
CT_LINK_BASE = 'https://www.communitytransit.org/route/%s%s'
CT_LINK_OPTIONS = ('', '/table', '/0/table')

FINAL_HTML = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <link href="index.css" rel="stylesheet" type="text/css"/>
        <link rel="icon" href="icon.ico">
        <title>ManyBusesAway</title>
    </head>
    <body>
        <h1>Completed Buses</h1>
        %s
        <table>%s
        </table>
        <p>%s</p>
        <span class="credit" onclick="window.open(\'%s\', \'_blank\')">%s</span>
    </body>
</html>'''
ROW_HTML = '\n%s<tr>%s</tr>' % (' ' * 12, '%s' * 6)
IMG_HTML = '<img src="%s" alt="%s" title="%s" width=100></img>'

NOTES = '''Only current King County Metro, Sound Transit, Everett Transit,
 Pierce Transit, and Community Transit routes are included.<br>
King County Metro and Sound Transit routes from immediately before the
 September 2024 service change are also included.<br>
Routes with <span class="discontinued">Discontinued</span> tag have been
 discontinued since their completion.<br>
Routes with <span class="delisted">Delisted</span> tag remain operational
 but are absent from public transit agency websites (possibly intentionally).'''

'''
This class allows for easier management of table rows and their associated data
and images.
'''
class RouteListing:
    def __init__(self, number, agency):
        '''
        Sets up self from number and agency strings. Plain RouteListings are
        only created in image-only setup; WebRouteListings created elsewhere.
        '''
        self.number = number.replace(' ', '')
        self.agency = agency
        if self.number.isnumeric():
            num = int(self.number)
            if not hasattr(self, 'css_class'):
                self.css_class = agency + str(num // 100)
            # Here begin a bunch of edge cases
            if agency == 'X':
                self.css_class = 'nonbus'
                self.agency = 'K'
            elif self.css_class == 'K0' and num in range(90, 100):
                self.css_class = 'special'
            elif agency == 'P':
                self.css_class = 'P'
            elif self.css_class == 'C4':
                self.css_class = 'C9'
            elif self.css_class == 'C5':
                raise AttributeError    # These routes shown by ST and CT both
        else:
            if self.number.startswith('DART'):
                # 775 must have DART palette, and so K7 is used for DART buses
                self.css_class = 'K7'
            elif self.agency == 'S':
                # Trains are all S0 palette
                self.css_class = 'S0'
            elif self.number == 'Stream':
                self.css_class = 'P'
            else:
                self.css_class = 'rapidride'
        # These four attributes are default values; they are usually set somehow
        self.start = ''
        self.dest = ''
        self.links = (None, None, None)
        self.nonexistence = 0
    def __lt__(self, other):
        '''
        Returns whether self is less than RouteListing other, for purposes of
        comparison.
        '''
        return self.position < other.position
    def position(self, indices):
        '''
        Returns position in ordering on website, sensitive to order of transit
        agencies taken from string indices.
        '''
        basenum = indices.index(self.agency) * 2000
        if not self.number.isnumeric():
            if self.number.startswith('DART'):
                return basenum + int(self.number.lstrip('DART'))
            return basenum - 256 + ord(self.number[0])
        return basenum + int(self.number)
    def __str__(self):
        '''Returns string representation of self, for debugging or -v.'''
        return ' '.join((
            'i–'[not self.img] + ' !*'[self.nonexistence],
            self.agency,
            self.number,
            '(' + self.css_class + ')',
            self.start,
            '⬌',
            self.dest))
    def to_html(self, imgdirectory):
        '''
        Returns this row's <tr> HTML element for the final table.
        This isn't the most elegant way to handle CSS classes when writing HTML
        by hand, but it is more simple when generating it.
        Handles special cases for visuals.
        string imgdirectory is used to make image links.
        '''
        # More notes may be needed in the future
        note = (
            ('none', ''),
            ('discontinued', 'Discontinued'),
            ('delisted', 'Delisted'))[self.nonexistence]
        if self.img:
            i_link = imgdirectory + '/' + self.img
            i_td = td(
                'none',
                IMG_HTML % (i_link, self.number, self.number),
                i_link,
                False)
        else:
            i_td = td('none', '')
        dnum = self.number
        # These are for special visuals
        if self.number.startswith('DART'):
            dnum = '<p class="dart">DART</p>' + dnum.lstrip('DART')
        elif self.css_class == 'S0':
            dnum = '<span class="circle c%s">%s</span>' % (dnum, dnum)
        elif self.css_class == 'C7':
            dnum = '<p class="swift">Swift</p>' + dnum
        elif self.number == 'Stream':
            dnum = '<p class="smallnum">Stream</p>'
        return ROW_HTML % (
            td('b-' + self.css_class, dnum, self.links[0]),
            td('n-' + self.css_class, self.start, self.links[1]),
            td('n-' + self.css_class, self.dest, self.links[2]),
            td(*note),
            td('complete' if self.img else 'incomplete', self.datetime),
            i_td)

'''
This class extends RouteListing to include additional data from site listings.
It inherits its constructor.
'''
class WebRouteListing(RouteListing):
    def set_termini_path(self, path, delimiter):
        '''
        Sets self.start and self.dest given string path
        (list of destinations, separated by string delimiter).
        This could not be done with regular regex; more logic is needed.
        '''
        # Catches King County edge cases
        if self.agency == 'K':
            match = re.match('Service between (.*) and (?:the | )(.*)', path)
            if match:
                self.start, self.dest = match.group(1), match.group(2)
                return
            destinations = path.split(delimiter)
            if destinations[0].startswith('Serves'):
                del destinations[0]
                self.css_class = 'schools'
                if 'School' in destinations[0]:
                    del destinations[0]
            self.start = destinations[0].lstrip().rstrip()
            self.dest = destinations[-1].lstrip().rstrip()
            return
        destinations = path.split(delimiter)
        self.start = destinations[0].lstrip().rstrip()
        self.dest = destinations[-1].lstrip().rstrip()
    def set_termini_iter(self, i, regex, delimiter=None):
        '''
        Sets self.start and self.dest given iterable of strings with those
        buried in redundant strings.
        re.Pattern regex is used to extract single terminus from string.
        This causes cryptic errors when imperfect regex is used to parse pages.
        string delimiter is used to split path as above, if applicable.
        '''
        self.start, self.dest = (regex.fullmatch(s).group(1) for s in i)
        if delimiter:
            self.start = self.start.split(delimiter)[-1].lstrip()
            self.dest = self.dest.split(delimiter)[-1].lstrip()
    def set_links(self, linkbase, linkpiece, linkoptions):
        '''
        Sets tuple self.links to string linkbase formatted with string linkpiece
        and each of the strings in tuple linkoptions.
        This allows each td in this RouteListing's tr to have a different but
        related link.
        '''
        self.links = tuple(linkbase % (linkpiece, o) for o in linkoptions)
    def find_image(self, images, imgdirectory):
        '''
        Sets self.img and self.datetime by checking images parameter for
        existence and local filesystem (in string imgdirectory) for stats.
        '''
        self.img = self.agency + self.number + '.jpg'
        if self.img in images:
            secs = os.stat(os.path.join(imgdirectory, self.img)).st_birthtime
            self.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
            images.remove(self.img)
        else:
            self.img = None
            self.datetime = 'Incomplete'

def http_request(url, data=None, verbose=False):
    '''
    Given string url, returns result of HTTP request in UTF-8.
    If dictionary data is specified, request will be POST, otherwise GET.
    Sanitizes output.
    '''
    h = {'User-Agent': 'Magic Browser', 'Content-Type': 'application/json'}
    if data:
        d = str(json.dumps(data)).encode('utf8')
        r = request.Request(url, method='POST', headers=h, data=d)
    else:
        r = request.Request(url, headers=h)
    if verbose:
        print(
            'Sending %s request to %s... ' % (r.get_method(), url),
            end='',
            flush=True)
    with request.urlopen(r) as file:
        if verbose:
            print('Response: %d' % file.status)
        result = file.read().decode('utf8')
        return result.replace('&amp;', '&').replace('–', '-').replace('\\', '')

def td(css_class, data, link=None, blank=True):
    '''
    Returns <td> HTML element given css_class, text/image data, and link.
    If link should open in same tab, blank should be False.
    '''
    if not link:
        return '<td class="%s">%s</td>' % (css_class, data)
    if blank:
        jsfunc = 'window.open(\'%s\', \'_blank\')' % link
    else:
        jsfunc = 'window.open(\'%s\', \'_self\')' % link
    return '<td class="%s" onclick="%s">%s</td>'\
        % (css_class, jsfunc, data)

def completenessHTML(route_listings):
    '''
    Given all route listings, returns regular Percentage Completeness heading
    if it's less than 100%, but returns Qualified Completeness heading when
    all non-snow-shuttle routes are complete, and returns Full Completeness
    heading when all routes are complete, with no exceptions.
    '''
    dt = datetime.fromtimestamp(time()).strftime('%-m/%-d/%y')
    total = 0
    completed = 0
    can_fc = True
    for rl in route_listings:
        if not rl.img:
            can_fc = False
        if rl.css_class != 'special' and not rl.nonexistence:
            total += 1
            completed += 1 if rl.img else 0
    if can_fc:
        return '<h2>Fully Complete on %s</h2>' % dt
    if completed == total:
        return '''<h2>Fully Complete* on %s</h2>
            <h3>*Excluding Unavailable Snow Shuttle</h3>''' % dt
    return '<h2>%d%% Complete, Updated %s</h2>' % (completed * 100 // total, dt)


def parse_args():
    '''
    This function uses an argparse.ArgumentParser to parse arguments.
    Returns argparse.Namespace which contains necessary flags and data.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='enable verbose mode')
    parser.add_argument(
        '-a',
        '--agencies',
        type=str,
        default='KSEPC',
        help='agencies to use and their order of appearance; default is KSEPC')
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default='index.html',
        help='output filename for HTML')
    parser.add_argument(
        'images',
        type=str,
        help='relative path to image directory')
    return parser.parse_args()
    
def main():
    '''
    Entry point of program.
    Parses arguments, gathers images that must be used while scraping buses
    from all transit agencies, creates route table.
    '''
    args = parse_args()
    route_listings = []
    # Sadly, route_listings.append cannot be modified
    if args.verbose:
        add_rl = lambda l, x: (print(x), l.append(x))
    else:
        add_rl = lambda l, x: l.append(x)
    images = set(x for x in os.listdir(args.images) if x.endswith('jpg'))

    html_trolley = ''                   # In case no request is sent
    if 'K' in args.agencies:
        js_kcm = http_request(KCM_URL, verbose=args.verbose)
        html_trolley = http_request(TROLLEY_URL, verbose=args.verbose)
        for m in re.finditer(re.compile(KCM_PATTERN), js_kcm):
            rl = WebRouteListing(m.group(2), 'K')
            rl.set_termini_path(m.group(3), ',')
            rl.set_links(KCM_LINK_BASE, m.group(1), KCM_LINK_OPTIONS)
            rl.find_image(images, args.images)
            if 'Route ' + rl.number in html_trolley:
                rl.css_class = 'trolley'
            add_rl(route_listings, rl)

    if 'S' in args.agencies:
        html_st = http_request(ST_URL, verbose=args.verbose)
        for m in re.finditer(re.compile(ST_PATTERN), html_st):
            rl = WebRouteListing(m.group(2), 'S')
            rl.set_termini_path(m.group(3), '-')
            rl.set_links(ST_LINK_BASE, m.group(1), ST_LINK_OPTIONS)
            rl.find_image(images, args.images)
            add_rl(route_listings, rl)

    if 'E' in args.agencies or 'P' in args.agencies:
        # Only used for Pierce Transit and Everett Transit Routes
        json_tripplanner = http_request(
            TRIPPLANNER_URL,
            {'version': '1.1', 'method': 'GetLines'},
            verbose=args.verbose)
        tp_lines_list = json.loads(json_tripplanner)['result']['lines']
        # This stores map of string rlid to generator over destination listings
        tp_lines_dict = dict()
        for i in tp_lines_list:
            if i['agencyId'] == 'ET':
                rlid = i['lineAbbr'][1:]
                tp_lines_dict[rlid] = (x['signage'] for x in i['directions'])
            elif i['agencyId'] == 'PT':
                #i['name'] doesn't work for 497
                dirs = tuple(x['signage'] for x in i['directions'])
                rlid = 'P' + dirs[0].partition(' ')[0]
                tp_lines_dict[rlid] = dirs
        tp_p = re.compile(TRIPPLANNER_PATTERN)

    if 'E' in args.agencies:
        html_et = http_request(ET_URL, verbose=args.verbose)
        for m in re.finditer(re.compile(ET_PATTERN), html_et):
            rl = WebRouteListing(m.group(2), 'E')
            rl.set_termini_iter(tp_lines_dict.pop('E' + m.group(2)), tp_p)
            # This error must be patched; again, Trip Planner data isn't great
            if rl.number == '6':
                rl.start = 'Waterfront'
            rl.set_links(ET_LINK_BASE, m.group(1), ET_LINK_OPTIONS)
            rl.find_image(images, args.images)
            add_rl(route_listings, rl)

    if 'P' in args.agencies:
        html_pt = http_request(PT_URL, verbose=args.verbose)
        for m in re.finditer(re.compile(PT_PATTERN), html_pt):
            rl = WebRouteListing(m.group(2), 'P')
            rl.set_termini_iter(tp_lines_dict.pop('P' + m.group(2)), tp_p, '/')
            rl.links = tuple(m.group(1) for x in range(3))
            rl.find_image(images, args.images)
            add_rl(route_listings, rl)

    if 'C' in args.agencies:
        html_ct = http_request(CT_URL, verbose=args.verbose)
        for m in re.finditer(re.compile(CT_PATTERN), html_ct):
            try:
                rl = WebRouteListing(m.group(1), 'C')
                rl.set_termini_path(m.group(2), '|')
                rl.set_links(CT_LINK_BASE, m.group(1), CT_LINK_OPTIONS)
                rl.find_image(images, args.images)
                add_rl(route_listings, rl)
            except AttributeError:      # Raised on Sound Transit duplicate
                continue

    # All remaining images are '*#.jpg' (delisted) or '#.jpg' (discontinued)
    while len(images):
        i = images.pop()
        rlid = i.rstrip('.jpg').lstrip('*')
        if rlid[0] not in args.agencies:
            if not (rlid[0] == 'X' and 'K' in args.agencies):
                continue                # Skip inapplicable images
        rl = RouteListing(rlid[1:], rlid[0])
        rl.nonexistence = i.startswith('*') + 1
        if rl.css_class == 'nonbus':
            rl.nonexistence = 0
        rl.img = i
        if rl.css_class in ('K8', 'K9') and not rl.number.startswith('DART'):
            rl.css_class = 'schools'    # Cannot check for "Serves" if absent
        secs = os.stat(os.path.join(args.images, i)).st_birthtime
        rl.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
        if 'Route ' + rl.number in html_trolley and rl.agency == 'K':
            rl.css_class = 'trolley'    # This is worth a shot
        add_rl(route_listings, rl)

    for rl in route_listings:
        # Precomputing this speeds up sorting
        rl.position = rl.position(args.agencies)
    if args.verbose:
        print('Sorting listings... ', end='', flush=True)
    route_listings.sort()
    if args.verbose:
        print('Done\nWriting HTML to %s... ' % args.output, end='', flush=True)
    fp = open(args.output, 'w')
    fp.write(FINAL_HTML % (
        completenessHTML(route_listings),
        ''.join([rl.to_html(args.images) for rl in route_listings]),
        NOTES,
        'https://github.com/6exagon/manybusesaway',
        re.search(r'([^\s]*\sv\d\.\d\..*)\s', __doc__).group(1)))
    fp.close()
    if args.verbose:
        print('Done')

if __name__ == '__main__':
    main()
