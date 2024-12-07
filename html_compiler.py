'''
This program is used to generate an HTML file to display completed buses.
Unfortunately, an HTML file with embedded JavaScript will not work for this;
file modification dates for photographs (lost when uploading to webhosting or
GitHub) are needed to render the page.
However, this progam is not standalone; it requires aforementioned photographs
(when they exist) to be inside a "./images" folder in the current working
directory.
This allows each type of route to have its own color scheme, among other things.
See README.md for more details.
'''

import os
import re
import urllib.request
from datetime import datetime
import time

# Current King County Metro URL, may be subject to change in the future
JS_KCM_URL = 'https://cdn.kingcounty.gov/-/media/king-county/depts/metro/'\
    + 'fe-apps/schedule/09142024/js/find-a-schedule-js.js'\
    + '?rev=b74ceeb7db85476cb2f92719c10e956f'
JS_KCM_TRIM = (
    '<option value="" selected="">Enter route or location</option>\\n    ',
    '\\n  </select>\\n\\x3c!-- end route selector --')
HTML_TROLLEY_URL = 'https://metro.kingcounty.gov/up/rr/m-trolley.html'
# This Sound Transit page's formatting is absolutely horrible and inconsistent,
# but it's seemingly the best resource there is
HTML_ST_URL = 'https://www.soundtransit.org/ride-with-us/schedules-maps'
HTML_ST_TRIM = (
    '<p>To print or download individual route schedules and maps click the '\
    + 'PDF.</p><ul><li>',
    '</li></ul></div>')
# No plaintext route terminals available anywhere on ET website officially
ET_PATH = 'everett_transit.csv'
HTML_PT_URL = 'https://piercetransit.org/'
HTML_PT_TRIM= (
    'Select Pierce Transit Route HERE</option>',
    '</select>')
HTML_CT_URL = 'https://www.communitytransit.org/maps-and-schedules/'\
    + 'maps-and-schedules-by-route'
HTML_CT_TRIM = (
    'var _routes = [{',
    '}];')

TIME_FORMAT = '%-m/%-d/%y %-H:%M'

IMG_PATH = 'images'

FINAL_HTML = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <link href="index.css" rel="stylesheet" type="text/css"/>
        <link rel="icon" href="icon.ico">
        <title>Completed Buses</title>
    </head>
    <body>
        <h1>Completed Buses</h1>
        %s
        <table>%s
        </table>
        <p>%s</p>
    </body>
</html>'''
ROW_HTML = '\n%s<tr>%s</tr>' % (' ' * 12, '%s' * 6)
# The following are for clickable <td> sections opening new tabs
IMG_LINK = IMG_PATH + '/%s'
IMG_HTML = '<img src="%s" alt="%s" title="%s" width=100></img>'
KCM_ROUTE_LINK = 'https://kingcounty.gov/en/dept/metro/routes-and-service/'\
    + 'schedules-and-maps/%s.html#%s'
KCM_ROUTE_OPTIONS = ('route-map', 'weekday', 'weekday-b')
ST_ROUTE_LINK = 'https://www.soundtransit.org/ride-with-us/routes-schedules/%s%s'
ST_ROUTE_OPTIONS = ('', '?direction=1', '?direction=0')
ET_ROUTE_LINK = 'https://everetttransit.org/DocumentCenter/View/%s#page=%s'
ET_ROUTE_OPTIONS = ('1', '2', '2')
# PT needs no link-building; links are included in the HTML
CT_ROUTE_LINK = 'https://www.communitytransit.org/route/%s%s/table'
CT_ROUTE_OPTIONS = ('', '/0', '')
NONE_OPTIONS = (None, None, None)       # This is for efficiency

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
        Sets up self from number and agency strings, This constructor is only
        called directly from image-only setup. self.nonexistence is not set
        here but by child class or by image setup.
        '''
        self.number = number
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
        self.start = ''
        self.finish = ''
        self.position = self.position() # Precomputing this speeds up sorting
    def position(self):
        '''
        Returns position in ordering on website, sensitive to order of transit
        agencies and special route status.
        '''
        basenum = 'KSEPC'.index(self.agency) * 2000
        if not self.number.isnumeric():
            if self.number.startswith('DART'):
                return basenum + int(self.number.lstrip('DART'))
            return basenum - 256 + ord(self.number[0])
        return basenum + int(self.number)
    def __lt__(self, other):
        '''
        Returns whether self is less than RouteListing other, for purposes of
        comparison.
        '''
        return self.position < other.position
    def __str__(self):
        '''Returns string representation of self, for debugging purposes.'''
        return self.number.ljust(8) + self.css_class + ' ' + self.start\
            + ' ⬌ ' + self.finish + ' (' + self.agency + ')'
    def link(self, param):
        '''
        This will be overridden by WebRouteListing.
        Thus, if routes are only found through images, they should have none.
        '''
        return None
    def to_html(self):
        '''
        Returns this row's <tr> HTML element for the final table.
        This isn't the most elegant way to handle CSS classes when writing HTML
        by hand, but it is more simple when generating it.
        '''
        # More notes may be needed in the future
        note = (
            ('none', ''),
            ('discontinued', 'Discontinued'),
            ('delisted', 'Delisted'))[self.nonexistence]
        if self.img:
            i_link = IMG_LINK % self.img
            i_td = td(
                'none',
                IMG_HTML % (i_link, self.number, self.number),
                i_link,
                False)
        else:
            i_td = td('none', '')
        q = {
            'K': KCM_ROUTE_OPTIONS,
            'S': ST_ROUTE_OPTIONS,
            'E': ET_ROUTE_OPTIONS,
            'P': NONE_OPTIONS,
            'C': CT_ROUTE_OPTIONS}[self.agency]
        dnum = self.number
        if self.number.startswith('DART'):
            dnum = '<p class="dart">DART</p>' + dnum.lstrip('DART')
        elif self.css_class == 'S0':
            dnum = '<span class="circle c%s">%s</span>' % (dnum, dnum)
        elif self.css_class == 'C7':
            dnum = '<p class="swift">Swift</p>' + dnum
        elif self.number == 'Stream':
            dnum = '<p class="smallnum">Stream</p>'
        if self.start != self.finish:
            return ROW_HTML % (
                td('b-' + self.css_class, dnum, self.link(q[0])),
                td('dest n-' + self.css_class, self.start, self.link(q[1])),
                td('dest n-' + self.css_class, self.finish, self.link(q[2])),
                td(*note),
                td('complete' if self.img else 'incomplete', self.datetime),
                i_td)
        return ROW_HTML % (
            td('b-' + self.css_class, dnum, self.link(q[0])),
            td('dest n-' + self.css_class, self.start, self.link(q[1]), span=True),
            '',
            td(*note),
            td('complete' if self.img else 'incomplete', self.datetime),
            i_td)

'''
This class extends RouteListing to automatically perform setup based on website
data, calls RouteListing constructor after custom setup.
'''
class WebRouteListing(RouteListing):
    def __init__(self, string, pattern, delimiter, agency):
        '''
        Sets up self from route listing string string, using re.Pattern pattern
        and string delimiter. Nonexistence flag is for main function to modify.
        '''
        string = string.replace('&amp;', '&').replace('–', '-').replace('\\', '')
        match = pattern.fullmatch(string)
        if not match:
            raise AttributeError
        if agency == 'E':
            self.number, path = match.group(1), match.group(2)
            self.et_link_num = match.group(3)
        elif agency == 'P':
            self.pt_link = match.group(1)
            self.number, path = match.group(2), match.group(3)
        else:
            self.number, path = match.group(1), match.group(2)
        if self.number.endswith('Line'):
            self.number = self.number.rstrip(' Line')[-1]
        elif self.number.endswith('Shuttle'):
            self.number = self.number.rstrip(' Shuttle')
        elif self.number == 'Stream':
            path = 'Tacoma - Spanaway'  # This is not listed for some reason
        elif not self.number.startswith('DART') and not self.number.isnumeric():
            raise AttributeError        # Do not include Water Taxi, etc. here
        super().__init__(self.number.replace(' ', ''), agency)
        self.set_terminals(path, delimiter)
        self.nonexistence = 0           # Obviously true for WebRouteListings
    def set_terminals(self, path, delimiter):
        '''
        Called from constructor, sets self.start and self.finish given string
        path (list of destinations, separated by string delimiter).
        '''
        # Catches King County edge cases
        if self.agency == 'K':
            match = re.match('Service between (.*) and (the | )(.*)', path)
            if match:
                self.start, self.finish = match.group(1), match.group(3)
                return
            destinations = path.split(delimiter)
            if destinations[0].startswith('Serves'):
                del destinations[0]
                self.css_class = 'schools'
                if 'School' in destinations[0]:
                    del destinations[0]
            self.start = destinations[0].lstrip().rstrip()
            self.finish = destinations[-1].lstrip().rstrip()
            return
        destinations = path.split(delimiter)
        self.start = destinations[0].lstrip().rstrip()
        self.finish = destinations[-1].lstrip().rstrip()
    def find_image(self, images):
        '''
        Sets self.img and self.datetime by checking images
        parameter for existence and local filesystem for stats.
        '''
        self.img = self.agency + self.number + '.jpg'
        if self.img in images:
            secs = os.stat(os.path.join(IMG_PATH, self.img)).st_birthtime
            self.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
            images.remove(self.img)
        else:
            self.img = None
            self.datetime = 'Incomplete'
    def link(self, param):
        '''Adds the correct HTML link to string text, with param in URL.'''
        if self.agency == 'S':
            return ST_ROUTE_LINK\
                % (self.number + '-line' * (self.css_class == 'S0'), param)
        elif self.agency == 'E':
            return ET_ROUTE_LINK % (self.et_link_num, param)
        elif self.agency == 'P':
            return self.pt_link
        elif self.agency == 'C':
            return CT_ROUTE_LINK % (self.number, param)
        elif self.css_class == 'rapidride':
            return KCM_ROUTE_LINK % (self.number + '-line', param)
        else:
            return KCM_ROUTE_LINK % (self.number.lstrip('DART').zfill(3), param)

def fetch_file(url):
    '''Given string url, returns contents of file fetched from it in UTF-8.'''
    r = urllib.request.Request(url, headers={'User-Agent': 'Magic Browser'})
    with urllib.request.urlopen(r) as file:
        return file.read().decode('utf8')

def td(css_class, data, link=None, blank=True, span=False):
    '''
    Returns <td> HTML element given css_class, text/image data, and link.
    If link should open in same tab, blank should be False.
    '''
    colspan = span * ' colspan="2"'
    if not link:
        return '<td class="%s"%s>%s</td>' % (css_class, colspan, data)
    if blank:
        jsfunc = 'window.open(\'%s\', \'_blank\')' % link
    else:
        jsfunc = 'window.open(\'%s\', \'_self\')' % link
    return '<td class="%s" onclick="%s"%s>%s</td>'\
        % (css_class, jsfunc, colspan, data)

def completenessHTML(route_listings):
    '''
    Given all route listings, returns regular Percentage Completeness heading
    if it's less than 100%, but returns Qualified Completeness heading when
    all non-snow-shuttle routes are complete, and returns Full Completeness
    heading when all routes are complete, with no exceptions.
    '''
    dt = datetime.fromtimestamp(time.time()).strftime('%-m/%-d/%y')
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
    
def main():
    '''
    Entry point of program.
    Gathers images that must be used, scrapes buses from both the Metro and
    Sound Transit websites, creates route table.
    '''
    in_angles = re.compile('<.*?>')
    route_listings = []
    images = set()
    for x in os.listdir(IMG_PATH):
        if x.endswith('.jpg'):
            images.add(x)

    js_metro = fetch_file(JS_KCM_URL)
    scan = js_metro.partition(JS_KCM_TRIM[0])[2].partition(JS_KCM_TRIM[1])[0]
    options = [in_angles.sub('', x) for x in scan.split('\\n    ')]
    html_trolley = fetch_file(HTML_TROLLEY_URL)
    pattern = re.compile('(.*) - (.*)')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, ',', 'K')
            rl.find_image(images)
            if 'Route ' + rl.number in html_trolley:
                rl.css_class = 'trolley'
            route_listings.append(rl)
        except AttributeError:
            continue

    html_st = fetch_file(HTML_ST_URL)
    scan = html_st.partition(HTML_ST_TRIM[0])[2].partition(HTML_ST_TRIM[1])[0]
    options = [in_angles.sub('', x) for x in scan.split('</li><li>')]
    pattern = re.compile('(.*)\\s\\((.*)\\).*\\n?')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, '- ', 'S')
            rl.find_image(images)
            route_listings.append(rl)
        except AttributeError:
            continue

    with open(ET_PATH, 'r') as f:
            scan = f.read()
    options = scan.split('\n')
    pattern = re.compile('(\\d*),(.*,.*),(\\d*)')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, ',', 'E')
            rl.find_image(images)
            route_listings.append(rl)
        except AttributeError:
            continue

    html_pt = fetch_file(HTML_PT_URL)
    scan = html_pt.partition(HTML_PT_TRIM[0])[2].partition(HTML_PT_TRIM[1])[0]
    options = scan.split('\n')
    pattern = re.compile('.*value="(.*)">Route (\\d*) \\|? (.*)</option>')
    streampattern = re.compile('.*value="(.*)">(Stream)().*</option>')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, '-', 'P')
            rl.find_image(images)
            route_listings.append(rl)
        except AttributeError:
            try:
                rl = WebRouteListing(o, streampattern, '-', 'P')
                rl.find_image(images)
                route_listings.append(rl)
            except AttributeError:
                continue

    html_ct = fetch_file(HTML_CT_URL)
    scan = html_ct.partition(HTML_CT_TRIM[0])[2].partition(HTML_CT_TRIM[1])[0]
    options = scan.split('},{')
    pattern = re.compile(
        '"route_id":"(\\d*)","route_name":"(.*)","route_short_name".*')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, '|', 'C')
            rl.find_image(images)
            route_listings.append(rl)
        except AttributeError:
            continue

    # All remaining images are '*#.jpg' (delisted) or '#.jpg' (discontinued)
    while len(images):
        i = images.pop()
        temp = i.rstrip('.jpg').lstrip('*')
        rl = RouteListing(temp[1:], temp[0])
        rl.nonexistence = i.startswith('*') + 1
        if rl.css_class == 'nonbus':
            rl.nonexistence = 0
        rl.img = i
        if rl.css_class in ('K8', 'K9') and not rl.number.startswith('DART'):
            rl.css_class = 'schools'    # Cannot check for "Serves" if absent
        secs = os.stat(os.path.join(IMG_PATH, i)).st_birthtime
        rl.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
        if 'Route ' + rl.number in html_trolley:
            rl.css_class = 'trolley'
        route_listings.append(rl)

    route_listings.sort()
    fp = open('index.html', 'w')
    fp.write(FINAL_HTML % (
        completenessHTML(route_listings),
        ''.join([rl.to_html() for rl in route_listings]),
        NOTES))
    fp.close()

if __name__ == '__main__':
    main()
