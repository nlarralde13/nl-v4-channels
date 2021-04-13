import base64, datetime, hashlib, hmac, json, requests, time, zlib
from pprint import PrettyPrinter
pp = PrettyPrinter().pprint  # Helps wrap things
import configparser

config = configparser.ConfigParser()
config.read("credentials.conf")

ROOT_URL = 'https://services.uplynk.com/api/v4'
channel_id = config.get('credentials', 'channel_id') # Channel ID you wish to Use
auth_header = True # True: New api/v4 pass the msg / sig through the header | False: Do it the old way

owner = config.get('credentials', 'userid') # uplynk owner id
api_key = config.get('credentials', 'apikey') # uplynk api key


# This helps create ISO 8601 Timestamps needed for the API
def convert_ts(utc_tstamp):
    """ Convert a utc timestamp to ISO 8601 formatted standard of YYYY-MM-DDThh:mm:ss.sZ
        :param utc_tstamp: The UTC timestamp to convert (expected milliseconds)
        # TODO: Perhaps support more than timestamps in milliseconds - but for now 99% of our timestamps
        # are in milliseconds

        :return: ISO 8601 formatted standard of YYYY-MM-DDThh:mm:ss.sZ
    """
    iso_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        _ts = float("{0:.3f}".format(utc_tstamp/1000.0))
        return "{}{}".format(datetime.datetime.utcfromtimestamp(_ts).strftime(iso_format)[:-4], "Z")
    except Exception:
        print ("BAD TIMESTAMP - CAN'T CONVERT: {}".format(utc_tstamp))
        raise

def call_api(api_service, method='get', **kwargs):
    #print ("\n<<<<<<<<<<<< NEW {} REQUEST >>>>>>>>>>>>\n".format(method.upper()))
    headers, params = None, None
    method = method.lower()

    url = '{}{}'.format(ROOT_URL, api_service)
    msg = {}
    msg['_owner'] = owner
    msg['_timestamp'] = int(time.time())
    msg = json.dumps(msg).encode()
    msg = base64.b64encode(zlib.compress(msg, 9)).strip()
    sig = hmac.new(api_key.encode(), msg, hashlib.sha256).hexdigest().encode()

    headers = {
            'Content-Type': 'application/json',
        }

    if auth_header:
        headers['Authorization'] = msg + b' ' + sig
        #print ("Using Header For Auth: {}".format(headers))
        params = {'headers': headers}
    else:
        #print ("Using Params For Auth: {}".format({'msg':msg, 'sig':sig}))
        params = {'params': {'msg':msg, 'sig':sig}, 'headers':headers}

    if method == 'get':
        response = requests.get(url, **params)
    elif method == 'patch':
        response = requests.patch(url, data=json.dumps(dict(**kwargs)), **params)
    elif method == 'post':
        response = requests.post(url, data=json.dumps(dict(**kwargs)), **params)
    elif method == 'delete':
        response = requests.delete(url, **params)

    print ("Called URL: {}".format(response.url))
    print ("\nRESPONSE SERVER ID: {}".format(response.headers.get('X-Services')))
    pp ("RESPONSE HEADERS: {}".format(response.headers))
    print ("\nResponse JSON:")

    if int(response.status_code) < 500:
        x = response.json()
        return x
    else:
        print ("\nREALLY BAD API ERROR:")
        pp(response.content)


def create_channel():
    post = {'desc':'the new channel', 'use_chsched':2,'slicer_id':'exampleid'}
    endpoint = '/channels'
    x = call_api(endpoint, method='post', **post)
    pp(x)
create_channel()
