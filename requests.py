'''
Handles fetching resources from different sources concurrently by HTTPS.
'''

import http.client
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from sys import stderr

HEADERS = {'User-Agent': 'ManyBusesAway', 'Content-Type': 'application/json'}
# For verbose printing, or in case of failure
V_MSG = 'HTTPS request for %s%s got response %s'

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
    sets list value for request to None, unless it is 3xx, in which case the
    indicated location is requested.
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
    Returns one resource gotten from url (either a string or a tuple, as
    described above).
    Makes and closes one http.client.HTTPSConnection.
    Returns None or the requested resource.
    '''
    body = None
    if not isinstance(url, str):
        # Usually just a string for GET requests, but was (url, body) for POST
        url, body = url
    dns_name, slash, p = url.partition('/')
    connection = http.client.HTTPSConnection(dns_name)
    returnval = send(connection, slash + p, body, verbose)
    connection.close()
    return returnval

def send(conn, page, body=None, verbose=False):
    '''
    Sends single request for string page (with optional body) over
    http.client.HTTPSConnection conn.
    If response code is not 200, prints message to stderr and returns None,
    unless it is 3xx, in which case the indicated location is requested by
    calling this function recursively.
    If verbose is True, prints message to stdout.
    '''
    if body:
        conn.request('POST', page, body, HEADERS)
    else:
        conn.request('GET', page, headers=HEADERS)
    resp = conn.getresponse()
    # conn.host is possibly undocumented, but it isn't private either, so it
    # should be ok, but it could be easily removed and is only used for verbose
    if resp.status == 200:
        if verbose:
            print(V_MSG % (conn.host, page, 'OK'))
        return resp.read().decode('utf-8').replace('\\', '')
    elif resp.status // 100 == 3:
        # All types of redirects should do this
        if verbose:
            print(V_MSG % (conn.host, page, resp.status) + ', redirecting...')
        # This is just to flush it out to avoid http.client.ResponseNotReady
        resp.read()
        return send(conn, resp.getheader('Location'), body, verbose)
    print(V_MSG % (conn.host, page, resp.status), file=stderr)
    return None
