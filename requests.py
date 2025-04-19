'''
Handles fetching resources from different sources concurrently by HTTPS.
'''

import http.client
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from sys import stderr

HEADERS = {'User-Agent': 'ManyBusesAway', 'Content-Type': 'application/json'}

def request_all(request_list, verbose=False):
    '''
    This function takes a list whose contents are either strings (URIs
    preceded by DNS names, i.e. website URLs) for GET requests, or tuples
    containing a string URL and a request body for POST requests.
    These are provided to http.client.HTTPSConnection.request. For speed,
    requests from the same DNS name aren't sent over the same HTTPS connection.
    Returns an iterable whose values are the response bodies, in the same order
    as the input.
    If a status code is anything other than 200, prints message to stderr and
    sets list value for request to None.
    If verbose is True, prints all requests.
    '''
    # This function uses a concurrent.futures.ThreadPoolExecutor to handle
    # multiple HTTP requests at once
    # This isn't real multithreading in CPython due to the GIL, but this
    # doesn't matter
    # http.client is not compatible with asyncio, and third-party libraries
    # are not used
    with ThreadPoolExecutor(len(request_list)) as executor:
        return executor.map(request_one, request_list, repeat(verbose))

def request_one(url, verbose=False):
    '''
    Returns one resource (either a string or a tuple, as described above).
    Makes and closes one http.client.HTTPSConnection.
    If response code is not 200, prints message to stderr and returns None.
    If verbose is True, prints message to stdout.
    '''
    body = None
    if not isinstance(url, str):
        # Usually just a string for GET requests, but was (url, body) for POST
        url, body = url
    dns_name, slash, page = url.partition('/')
    connection = http.client.HTTPSConnection(dns_name)
    if body:
        connection.request('POST', slash + page, body, HEADERS)
    else:
        connection.request('GET', slash + page, headers=HEADERS)
    resp = connection.getresponse()
    if resp.status == 200:
        if verbose:
            print('HTTPS request for %s got response OK' % url)
        returnval = resp.read().decode('utf-8').replace('\\', '')
    else:
        print(
            'HTTPS request for %s got response %d' % (url, resp.status),
            file=stderr)
        returnval = None
    connection.close()
    return returnval
