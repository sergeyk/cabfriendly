from datetime import datetime
from django.db import models
from django.contrib.auth.models import User 
from django.db.models import Q

import util

class Ride(models.Model):
  MAX_PEOPLE = 4 # hard-coded for taxis
  MAX_START_DISTANCE = 0.25 # miles 
  MAX_END_DISTANCE = 2 # miles 
  # TODO: set programatically as function of ride distance

  description = models.CharField(max_length=144, blank=True, null=True)
     
  def get_sr_for_user(self,user):
    """
    Returns the SearchRequest that belongs to this user in this Ride.
    Note that filled_out is required to have been called previously
    """
    assert(self.requests)
    for req in self.requests:
      if req.user == user:
        return req
       
    return None

  def in_bounds(self):
    """
    This function returns true if self.search_request is within bounds. Note that
    filled_out(user_sr) must have been previously called
    """
    #check expiration time bounds
    assert(self.search_request)
    if self.num_people > Ride.MAX_PEOPLE:
    	return False
    
    main_req = self.requests[0]
    for req in self.requests[1:]:
        if main_req.start_time > req.expiration_time \
           or main_req.expiration_time < req.start_time:
           return False
    
    return self.start_distance <= Ride.MAX_START_DISTANCE and \
          self.end_distance <= Ride.MAX_END_DISTANCE
      
  # TODO: figure out how to denormalize this table
  def filled_out(self, sr=None):
    """
    Fills out fields of self with ride info, assembled from the requests.
    If a SearchRequest is passed in, also returns distances to start and end.
    """

    requests = self.requests = self.searchrequest_set.all().order_by('id')
    # TODO: should we throw an exception here?
    if not self.requests:
       return None
    
    # Basic info
    self.riders = [req.user for req in requests]
    self.num_people = len(self.riders)
    self.poster = requests[0].user
	
    # Start and end locations are from the original request
    self.start_lat = requests[0].start_lat
    self.start_long = requests[0].start_long
    self.end_lat = requests[0].end_lat
    self.end_long = requests[0].end_long

    # Start time is the max of all the requests
    self.start_time = max((r.start_time for r in requests))
    
    # Expiration time is the min of all the requests
    # TODO: this does not seem like fair behavior
    self.expiration_time = min((r.expiration_time for r in requests))

    # If sr is passed in, also calculate distances:
    if (sr):
      self.update_with_sr(sr)
    
    return self 

  def update_with_sr(self, sr):
    '''
    Adds the following to a filled-out Ride
     - distance to the original request location
     - distance to the closest destination
    '''
    self.search_request = sr
    self.start_distance = util.distance(
        (sr.start_lat,sr.start_long),
        (self.requests[0].start_lat, self.requests[0].start_long))
    self.end_distance = min([
      util.distance(
        (sr.end_lat,sr.end_long),
        (r.end_lat, r.end_long)) for r in self.requests])
        
  @classmethod
  def get_all_rides(cls):
    """Test method, return all rides ever."""
    q = SearchRequest.objects.\
          filter(ride__id__isnull=False)
    unique_rides = set((sr.ride for sr in q))
    return [ride.filled_out() for ride in unique_rides] 

  @classmethod
  def get_all_rides_for_user(cls, user):
    """
    Return all Rides that the user has participated in.
    """
    # NOTE: assuming that a user wouldn't have multiple search requests
    # assigned to the same ride.
    srs = user.searchrequest_set.filter(ride__id__isnull=False)
    return [sr.ride.filled_out(sr) for sr in srs] 

  @classmethod
  def get_results_for_searchrequest(cls, sr):
    """
    Return all active Rides that match the user's search:
    - expiration_time >= request.start_time
    - expiration_time <= request.expiration_time
    - start_time <= request.start_time
    - start location within radius of request's start location
    - end_location within radius of requests's end location
    - num_people allows the user to participate
    """
    # First, build up the initial query: num_people and location
    query = Q(ride__isnull=False) &\
        Q(num_people__lte=(Ride.MAX_PEOPLE-sr.num_people)) &\
        Q(start_lat__lte=(sr.start_lat + Ride.MAX_START_DISTANCE*0.0145)) &\
        Q(start_lat__gte=(sr.start_lat - Ride.MAX_START_DISTANCE*0.0145)) &\
        Q(start_long__lte=(sr.start_long + Ride.MAX_START_DISTANCE*0.02)) &\
        Q(start_long__gte=(sr.start_long - Ride.MAX_START_DISTANCE*0.02)) &\
        Q(end_lat__lte=(sr.end_lat + Ride.MAX_END_DISTANCE*0.0145)) &\
        Q(end_lat__gte=(sr.end_lat - Ride.MAX_END_DISTANCE*0.0145)) &\
        Q(end_long__lte=(sr.end_long + Ride.MAX_END_DISTANCE*0.02)) &\
        Q(end_long__gte=(sr.end_long - Ride.MAX_END_DISTANCE*0.02))

    exclusions = Q(user__id__exact=sr.user.id) |\
        Q(start_time__gt=sr.expiration_time) |\
        Q(expiration_time__lte=sr.start_time)
    srs = SearchRequest.objects.filter(query).exclude(exclusions)
    unique_rides = set((x.ride for x in srs))
    unique_rides = (ride.filled_out(sr) for ride in unique_rides)
    unique_rides = (ride for ride in unique_rides if ride.in_bounds())
    return unique_rides

  def __unicode__(self):
    return "ID: %s\tDescription: %s" % ( self.id, self.description )
  
class SearchRequest(models.Model):
    # foreign keys (id is automatically provided)
    user = models.ForeignKey(User)
    ride = models.ForeignKey(Ride, blank=True, null=True)

    # data 
    start_lat = models.FloatField()
    start_long = models.FloatField()
    end_lat = models.FloatField()
    end_long = models.FloatField()
    submission_time = models.DateTimeField()
    start_time = models.DateTimeField()
    expiration_time = models.DateTimeField()
    num_people = models.IntegerField()

    def __unicode__(self):
        return "User: %s Ride: %s start_time: %s num_people: %s"%(
          self.user, self.ride, self.start_time, self.num_people)
    
