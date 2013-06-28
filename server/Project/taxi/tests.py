from django.utils import unittest
from taxi.models import *

class SearchRequestTestCase(unittest.TestCase):
  # first, the database is flushed to the state after syncdb was called.
  # then, the following fixtures are also loaded
  fixtures = []

  def setUp(self):
    None

  def testCreateWithoutRide(self):
    sr_info = {
        "ride": None,
        "user": User.objects.all()[0],
        "num_people":1,
        "start_lat": 0.0,
        "start_long": 0.0,
        "end_lat": 0.0,
        "end_long": 0.0,
        "submission_time": "2012-12-01 04:00:00",
        "start_time":"2012-12-01 04:00:00",
        "expiration_time":"2012-12-01 04:30:00"
    }
    sr = SearchRequest(**sr_info)
    #sr.save()
    assert(sr.ride == None)

  def testCreateWithRide(self):
    ride = Ride()
    assert(len(ride.searchrequest_set.all())==0)

    sr_info = {
        "ride": ride, 
        "user": User.objects.all()[0],
        "num_people":1,
        "start_lat": 0.0,
        "start_long": 0.0,
        "end_lat": 0.0,
        "end_long": 0.0,
        "submission_time": "2012-12-01 04:00:00",
        "start_time":"2012-12-01 04:00:00",
        "expiration_time":"2012-12-01 04:30:00"
    }
    sr = SearchRequest(**sr_info)
    sr.save()
    assert(sr.ride)
    assert(sr.ride == ride)
    assert(len(sr.ride.searchrequest_set.all())==1)

    # checking that we can chain commands
    assert(len(sr.ride.searchrequest_set.all().order_by('id'))==1)

  def testMatchingRidesSearch(self):
    ride = Ride()
    assert(len(ride.searchrequest_set.all())==0)

    grant = (37.8676, -122.2751)
    fisherman = (37.8090, -122.4150)
    sr_info = {
        "ride": ride, 
        "user": User.objects.all()[0],
        "num_people":1,
        "start_lat": 0.0,
        "start_long": 0.0,
        "end_lat": 0.0,
        "end_long": 0.0,
        "submission_time": "2012-12-01 04:00:00",
        "start_time":"2012-12-01 04:00:00",
        "expiration_time":"2012-12-01 04:30:00"
    }
    sr = SearchRequest(**sr_info)
    sr.save()
    assert(sr.ride)
    assert(sr.ride == ride)
    assert(len(sr.ride.searchrequest_set.all())==1)
