#! /usr/bin/python

'''
Example OAuth client for use with Sinatra OAuth
'''

# This is a modified version of the Fire Eagle Python tutorial

import httplib
import oauth
import pickle # for storing access token to file
import cgi # for playing with query strings
import urlparse

# file to store access token
TOKEN_FILE = './access_token.pkl'

SERVER = 'localhost'
PORT = 4567
HOST = SERVER + ":" + str(PORT)

REQUEST_TOKEN_URL = "http://" + HOST + "/oauth/request_token"
ACCESS_TOKEN_URL = "http://" + HOST + "/oauth/access_token"
AUTHORIZATION_URL = "http://" + HOST + "/oauth/authorize"
QUERY_API_URL = "http://" + HOST + "/messages.json"

# key and secret you got from Sinatra OAuth when registering an application
CONSUMER_KEY = 'kwCDvTxbVCfRV9fj4hJeg'
CONSUMER_SECRET = '25WMooFr6ZVa5Z1axw0qQTyYUokBOq6apxWFaYyrY'

def pause(prompt='hit <ENTER> to continue'):
    return raw_input(prompt+'\n')

# pass an oauth request to the server (using httplib.connection passed in as param), return the response as a string
def fetch_response(oauth_request, connection, debug=True):
    url= oauth_request.to_url()
    o = urlparse.urlparse(url)
    connection.request(oauth_request.http_method, 
        o.path + '?' + o.query)
    response = connection.getresponse()
    s=response.read()
    if debug:
        print 'requested URL: %s' % url
        print 'server response: %s' % s
    return s

# main routine
def test_sinatraoauth():
    
    # setup
    connection = httplib.HTTPConnection(SERVER, PORT) # a connection we'll re-use a lot
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1() # HMAC_SHA1 is Sinatra OAuth's preferred hashing method
    
    # check if we've got a stored token
    try:
        pkl_file=open(TOKEN_FILE, 'rb')
        token=pickle.load(pkl_file)
        pkl_file.close()
    except:
        token=None
    if token:
        print 'You have an access token: %s' % str(token.key)
    else:
        # get request token
        print '* Obtain a request token ...'
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_url=REQUEST_TOKEN_URL) # create an oauth request
        oauth_request.sign_request(signature_method, consumer, None) # the request knows how to generate a signature
        resp=fetch_response(oauth_request, connection) # use our fetch_response method to send the request to Sinatra OAuth
        print '\nSinatra OAuth response was: %s' % resp
        # if something goes wrong and you get an unexpected response, you'll get an error on this next line
        token=oauth.OAuthToken.from_string(resp) # parse the response into an OAuthToken object
        print '\nkey: %s' % str(token.key)
        print 'secret: %s' % str(token.secret)
    
        # authorize the request token
        print '\n* Authorize the request token ...'
        # create a new OAuthRequest, this time for the AUTHORIZATION_URL
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_url=AUTHORIZATION_URL)
        oauth_request.sign_request(signature_method, consumer, token)
        # this time we'll print the URL, rather than fetching from it directly
        full_url=oauth_request.to_url()
        print 'Authorization URL:\n%s' % full_url
        pause('Please go to the above URL and authorize the app -- hit <ENTER> when done.')
    
        # get access token
        print '\n* Obtain an access token ...'
        # note that the token we're passing to the new OAuthRequest is our current request token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_url=ACCESS_TOKEN_URL)
        oauth_request.sign_request(signature_method, consumer, token)
        resp=fetch_response(oauth_request, connection) # use our fetch_response method to send the request to Sinatra OAuth
        print '\nSinatra OAuth response was: %s' % resp
        # now the token we get back is an access token
        token=oauth.OAuthToken.from_string(resp) # parse the response into an OAuthToken object
        print '\nkey: %s' % str(token.key)
        print 'secret: %s' % str(token.secret)
        # try to store the access token for later user
        pkl_file=open(TOKEN_FILE, 'wb')
        pickle.dump(token, pkl_file)
        pkl_file.close()
        pause()
    # end if no token
    
    # access protected resource
    print '\n* Access a protected resource ...'
    print 'To try a query enter somthing like: %s' % QUERY_API_URL
    s=pause('enter a URL (empty string or <ENTER> to quit):')
    while s:
        try:
            (path, query)=s.split('?',1)
            params=clean_params( cgi.parse_qs(query) )
        except ValueError:
            path=s
            params={}
        #if path.endswith('update'): # use POST for updates
        #    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_method='POST', token=token, http_url=path, parameters=params)
        #else:
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_url=path, parameters=params)
        oauth_request.sign_request(signature_method, consumer, token)
        #if path.endswith('update'): # use POST for updates
        #    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"} # need this?
        #    post_data=oauth_request.to_postdata()
        #    print '\nPOSTing to %s' % path
        #    print 'sending headers: %s' % headers
        #    print 'sending data: %s' % post_data
        #    connection.request('POST', path, post_data, headers)
        #    s = connection.getresponse().read()
        #else:
        full_url=oauth_request.to_url()
        print '\nGETing from : %s' % full_url
        s=fetch_response(oauth_request, connection)

        print '\nthe server says: %s' % s
        s=pause('\nenter a URL (empty string or <ENTER> to quit):')
        
# cgi.parse_qs returns values as a list -- we want single values, we'll just keep the first for now...
def clean_params(p):
    for k in p.keys():
        p[k]=p[k][0]        
    return p
        
# app entry point
if __name__ == '__main__':
    test_sinatraoauth()
    print 'Done.'
