#!/usr/bin/env python

import time
import urllib
import urllib2, cookielib, re, os, sys
import re
from datetime import datetime, timedelta
import traceback

import random

import numpy as np

# XXX: If you are submitting a form, you must visit the page where the form
# lives. After doing so, use get_crsf_token to extract the token. You must pass
# it as the parameter 'csrfmiddlewaretoken' in the params dictionary that you
# are posting with.

HEADER_MINUS_REFERER = [('Content-Type', 'application/x-www-form-urlencoded'),
                        ('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 3.5.30729)')]

user_ids = { 'Harry': 100003254610163,
             'Brittany': 100003222494228,
             'Dorothy': 100003241573645,
             'Carl': 100003208520700,
             'Bob': 100003221077806 }
# user_ids = { 'Brittany': 100003222494228,
#              'Bob': 100003221077806 }
location = 'http://cabfriendly.com/'
# location = 'http://ec2-204-236-145-46.us-west-1.compute.amazonaws.com/'
# all_users = [ CabFriendlyUser('Harry', 100003254610163)
#               ,CabFriendlyUser('Brittany', 100003222494228)
#               ,CabFriendlyUser('Dorothy', 100003241573645)
#               ,CabFriendlyUser('Carl', 100003208520700)
#               ,CabFriendlyUser('Bob',100003221077806)
#               ]

class Transaction(object):
    def __init__(self):
        self.custom_timers = {}
        which_user = random.randint(0, len(user_ids) - 1)
        which_key = user_ids.keys()[which_user]
        self.user = CabFriendlyUser(which_key, user_ids[which_key])
        self.user.login(location)

    def run(self):
        request_results = self.search_request(location, self.user)
        self.add_ride(location, request_results, self.user)

    def search_request(self, root, user):
        """
        This function makes a SearchRequest. It returns the HTML response
        """
        loc = root + 'rides/search/'

        # Django complains if the refer is not correct
        user.opener.addheaders = HEADER_MINUS_REFERER + \
            [('Referer', root + 'rides/request/')]

        start_time = time.time()
        user.opener.open(root + 'rides/request/')
        latency = time.time() - start_time
        self.custom_timers['request'] = latency

        token = get_crsf_token(user)

        # need to POST these params
        now = datetime.now()
        delta = timedelta(minutes = 42)
        now_str = format_date(now)
        exp_str = format_date(now + delta)
        
        # form = {
        #     'start_lat': random.rand(),
        #     'start_long': u'3.3',
        #     'end_lat': u'4.2',
        #     'end_long': u'4.2',
        #     'start_time': now_str,
        #     'expiration_time': exp_str,
        #     'num_people': u'1',
        #     'csrfmiddlewaretoken': token
        #     }


        form = {
            'start_lat': unicode(random.random() * 180 - 90),
            'start_long': unicode(random.random() * 180 - 90),
            'end_lat': unicode(random.random() * 180 - 90),
            'end_long': unicode(random.random() * 180 - 90),
            'start_time': now_str,
            'expiration_time': exp_str,
            'num_people': u'1',
            'csrfmiddlewaretoken': token
            }

#         form = {
#             'start_lat': unicode(0.09 * np.random.randn() * 180 - 90),
#             'start_long': unicode(0.09 * np.random.randn() * 180 - 90),
#             'end_lat': unicode(0.09 * np.random.randn() * 180 - 90),
#             'end_long': unicode(0.09 * np.random.randn() * 180 - 90),
#             'start_time': now_str,
#             'expiration_time': exp_str,
#             'num_people': u'1',
#             'csrfmiddlewaretoken': token
#             }

        params = urllib.urlencode(form)
        try:
            status_log("(%s) starting search request" % user.name)
            start_time2 = time.time()
            result = user.opener.open(loc, params)
            latency2 = time.time() - start_time2
            self.custom_timers['search_request'] = latency2
            status_log("(%s) search_request: %s" % (user.name, latency2))
        except Exception as exception:
            print "got an exception (search request)"
            status_log(exception)
            status_log(exception.args)
            print traceback.format_exc()
            sys.exit(1)
        
            # If a ride doesn't exist return false.
            # Otherwise, try first available ride
        data = result.read()
        # print data
        return filter_rides_html(data)

    def add_ride(self, root, result, user):
        """
        If there is a matching one, it joins the first ride. If there isn't, it
        makes a new ride.

        Requirements: called search_request (or just pass result=False)
        """
        # print result
        if result:
            status_log("(%s) in result" % user.name)
            while True:
                try:
                    status_log("(%s) Accessing join ride form %srides/%s/" %
                               (user.name,root, result[0]))
                    start_time = time.time()
                    http_res = user.opener.open("%srides/%s/" % (root, result[0]))
                    latency = time.time() - start_time
                    self.custom_timers['ride_info'] = latency
                    http_read = http_res.read()
                    if "Error" in http_read:
                        status_log("(%s) Error: Couldn't access the ride" % user.name)
                        return False
                    elif "Sorry" in http_read:
                        status_log("(%s) Error: can't view ride" % user.name)
                        return False

                    # status_log("Sleeping for a second")
                    # time.sleep(2)
                    # logging join time
                    # XXX: This includes the search time if the ride fails
                    status_log("(%s) Submitting join ride form %srides/join/%s/" %
                               (user.name,root, result[0]))
                    start_time = time.time()
                    http_res = user.opener.open("%srides/join/%s/" % (root, result[0]))
                    latency = time.time() - start_time
                    self.custom_timers['join_ride'] = latency

                    http_data = http_res.read()
                    # print "-------"
                    # print http_data
                    # print "-------"
                    if "Sorry" in http_data:
                        # back in the search page
                        status_log("(%s) Couldn't join ride. Searching again" % user.name)
                        result = filter_rides_html(http_data)
                        if not result:
                            status_log("(%s) No valid rides (in loop). Creating a new one" % user.name)
                            return self.create_new_ride(root, user)
                        else:
                            status_log("(%s) Attempting to join anotherride %s" %
                                       (user.name, result[0]))
                    elif "Thank" in http_data:
                        status_log("(%s) Successfully joined the ride" % user.name)
                        return True
                    else:
                        print "------------------------------"
                        print http_data
                        print "------------------------------"
                        status_log("(%s) Unhandled error" % user.name)
                except Exception as e:
                    print "Exception ",user.name
                    print traceback.format_exc()
                    print type(e)
                    print e.args
                    print e
                    sys.exit(1)
        else:
            status_log("(%s) No valid rides. Creating a new one" % user.name)
            new_ride = self.create_new_ride(root, user)
            return new_ride

    def create_new_ride(self, root, user):
        status_log("(%s) Visitng new ride" % user.name)

        # pulling the join page
        start_time = time.time()
        http_res = user.opener.open(root + 'rides/new/')
        latency = time.time() - start_time
        self.custom_timers['new_form'] = latency
        
        token = get_crsf_token(user)
        form = { 'description' : 'sup dawg, ride wit me homeboy',
                 'csrfmiddlewaretoken': token}
        params = urllib.urlencode(form)
        status_log("(%s) Submitting form " % user.name)

        # submitting the form
        start_time = time.time()
        result = user.opener.open(root + 'rides/new/', params)
        latency = time.time() - start_time
        self.custom_timers['new_submit'] = latency

        http_res = result.read()

        return "Thank" in http_res

        
def status_log(msg):
    print >> sys.stderr, "[%s]:\t%s" % (datetime.now(), msg)
    pass


class CabFriendlyUser():
    def __init__(self, name, fb_id):
    	self.name = name
    	self.id = fb_id
        cj = cookielib.CookieJar()
        self.cookies = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener( self.cookies )
        urllib2.install_opener(opener)

        opener.addheaders = HEADER_MINUS_REFERER + \
            [('Referer', 'http://login.facebook.com/login.php')]
        self.opener = opener
 
    def logout(self):
        usock = self.opener.open('http://cabfriendly/facebook/logout/')
        
    def login(self, root=None):
        if root:
            loc = root + 'test/%d/' % self.id
        else:
            loc = 'http://cabfriendly.com/test/%d/' % self.id
            # loc = 'http://ec2-204-236-145-46.us-west-1.compute.amazonaws.com/test/%d/' % (self.id)
        usock = self.opener.open(loc)
        if "Welcome" in usock.read():
            status_log("%s logged in to CabFriendly." % self.name)
        else:
            print "CabFriendly login failed for", self.name
            print usock.read()
            sys.exit()
            
def pad_time(num):
    if num < 10:
        return "0%d" % (num)
    return "%d" % (num)

def format_date(a_time):
    """
    Converts a datetime object into a readable object that is submitted in a
    form. Required for any date form submissions
    """
    out_str = "%s-%s-%s %s:%s:%s" % (a_time.year,
                                     pad_time(a_time.month),
                                     pad_time(a_time.day),
                                     pad_time(a_time.hour),
                                     pad_time(a_time.minute),
                                     "00")
    return out_str

def get_crsf_token(user):
    """
    Returns the CSRF token from the user's opener. Requires that the user
    requests a form.
    """
    token = [x.value for x in user.cookies.cookiejar if x.name == 'csrftoken'][0]
    return token


def filter_rides_html(html_data):
    if "Sorry" in html_data:
        return False
    else:
        matches = re.findall(r'rides/\d+/', html_data)
        return map(lambda x: x.replace('rides/','').replace('/',''), matches)


def main():
    trans = Transaction()
    trans.run()
    print trans.custom_timers

if __name__ == '__main__':
    main()
