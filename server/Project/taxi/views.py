from datetime import datetime

from django.utils import simplejson

from django.db import transaction

from django.contrib import messages

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic.simple import direct_to_template

from django.contrib.auth.views import logout

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.core.mail import send_mass_mail

from facebook.models import FacebookProfile
from facebook.backend import *
from facebook.views import login, callback, test_login

from forms import *
from models import *

THANK_YOU_MESSAGE = "Thank you for submitting your request! You will receive an e-mail notification when someone joins."
OUR_EMAIL = "cabfriendly@gmail.com"

@login_required
def home(request):
    return render_to_response('home.html',
                              context_instance=RequestContext(request))    

def all_rides(request):
    """
    Show all rides rides in the database (for testing).
    """
    context_instance=RequestContext(request)
    data = {
        'subtitle': 'Current Rides',
        'matching': False,
        'rides': Ride.get_all_rides()}
    return render_to_response('rides.html', data,
        context_instance=context_instance)

def current_rides(request):
    """
    Show all rides that the user has ever taken.
    """
    context_instance=RequestContext(request)
    user = context_instance['user']
    data = {
        'subtitle': 'Current Rides',
        'matching': False,
        'rides': Ride.get_all_rides_for_user(user)}
    return render_to_response('rides.html', data,
        context_instance=context_instance)
       
def join_ride(request, ride_id):
    """
    Given a ride_id and a previous search request, allow the user to join the
    ride.

    Required: User submitted a search request
    """
    context_instance = RequestContext(request)
    user = context_instance['user']
    ride = Ride.objects.get(pk=ride_id)
    if '_search_request' in request.session:
        # user is attempting to add this ride
        sr_post = request.session['_search_request']
        rr_form = RideRequestForm(sr_post)
        user_sr = rr_form.save(commit = False)
        user_sr.user = context_instance['user']
        ride = ride.filled_out(user_sr)
        if ride.in_bounds():
            user_sr.submission_time = datetime.now()
            # return HttpResponse(str(ride.num_of_people() + 1))
            if (ride.num_people + user_sr.num_people) <= Ride.MAX_PEOPLE:
                user_sr.ride = ride
            # TODO: Make sure the ride is not full and this person can still join
            #       the ride. If not, then throw an error.
            # FIXME: Potential race condition
                with transaction.autocommit():
                    user_sr.save()
                
                ride = ride.filled_out(user_sr)
                if ride.num_people > Ride.MAX_PEOPLE:
                    user_sr.delete()
                    messages.add_message(request, messages.ERROR,
                                         "Sorry, someone beat you to that ride!" +
                                         " Pick another or create a new ride.")
                    return redirect('/rides/search/')
            else:
                messages.add_message(request, messages.ERROR,
                                     "Sorry, someone beat you to that ride!" +
                                     " Pick another.")
                return redirect('/rides/search/')
                
            del request.session['_search_request']
            messages.add_message(request, messages.SUCCESS, "Thank you for" +
                                 " joining a ride! Coordinate with the others" +
                                 " to meet and share the fare!" )
            
            #Send e-mail notification to other riders
            subject = '%s %s has joined your ride!' % (user.first_name, user.last_name)
            body = '%s has joined a ride you are a part of at CabFriendly.com.  Go to http://cabfriendly.com/rides/%d/ to view updated details and coordinate the ride.' % (user.first_name, ride.id)
            emails = []
            for rider in ride.riders:
                if rider != user:
                    emails.append((subject, body, OUR_EMAIL, [rider.email]))
            send_mass_mail(emails, fail_silently=False)            
            return redirect('/rides/%d/' % ride.id)
        else:
            messages.add_message(request, messages.ERROR, "Sorry, you aren't" +
                                 " compatible with this ride." )
            return redirect('/rides/search/')
    else:
        return redirect('/rides/current/')

    return redirect('/')

def drop_ride(request, ride_id):
    """
    This function drops a user from a ride if they are part of it. Otherwise, it
    does nothing and reports an error.
    """
    context_instance = RequestContext(request)
    user = context_instance['user']
    query = Q(ride__id=ride_id) &\
        Q(user__id=user.id)
    sr = SearchRequest.objects.filter(query)
    if sr:
        sr = sr[0]
        ride = sr.ride
        		
        sr.delete()
        messages.add_message(request, messages.SUCCESS,
                             "Success! You were removed from the ride.")
        #Send e-mail notification to other riders
        subject = '%s %s has left your ride' % (user.first_name, user.last_name)
        body = 'Sorry, but %s has left a ride you are a part of at CabFriendly.com.  Go to http://cabfriendly.com/rides/%d/ to view updated details and coordinate the ride.' % (user.first_name, ride.id)
        emails = []
        ride.filled_out()
        for rider in ride.riders:
            if rider.id != user.id:
                emails.append((subject, body, OUR_EMAIL, [rider.email]))
        send_mass_mail(emails, fail_silently=False)
    else:
        messages.add_message(request, messages.WARNING,
                             "You actually weren't part of ride %s to begin with :)"
                             % (ride_id))
    return redirect('/')
    
def ride_info(request, ride_id):
    """
    Page displaying ride information, along with a chat window.
    First, confirm that the user is or has been part of this ride.
    Then, fetch the ride information.
    """
    context_instance = RequestContext(request)
    user = context_instance['user']
    ride = Ride.objects.get(pk=ride_id).filled_out()

    # If they have submitted a request and it is in bounds of the ride, let them
    # see this ride.
    # Next, check if they are part of this ride. If they are, let them see it.
    # Otherwise, don't let them see it
    user_sr = ride.get_sr_for_user(user)
    if not user_sr:
        if '_search_request' in request.session:
            # user is attempting to add this ride
            sr_post = request.session['_search_request']
            rr_form = RideRequestForm(sr_post)
            user_sr = rr_form.save(commit = False)
            user_sr.user = context_instance['user']
            ride.update_with_sr(user_sr)
            if not ride.in_bounds():
                messages.add_message(request, messages.ERROR,
                                     "Error: This ride is out of your bounds." +
                                     " You do not have access to this ride.")
                return redirect('/rides/search/')
        else:
            messages.add_message(request, messages.ERROR,
                             "Error: You do not have access to this ride.")
            return redirect('/')
    else:
    	ride.update_with_sr(user_sr)
    	
    # encrypt the ride id and user_name
    enc_name = 'not implemented'
    enc_ride_id = 0

    data = {
      'subtitle': 'Ride Details',
      'ride': ride,
      'enc_name': enc_name,
      'enc_ride_id': enc_ride_id,
      'user_names': ','.join(['"%s %s"' % (rider.first_name, rider.last_name) for rider in ride.riders]),
      'start_latlongs': ['new google.maps.LatLng(%f, %f)' % (req.start_lat, req.start_long) for req in ride.requests],
      'end_latlongs': [ 'new google.maps.LatLng(%f, %f)'  % (req.end_lat, req.end_long) for req in ride.requests],
      'user_in_ride': user in ride.riders}
    
    return render_to_response('detail.html', data,
        context_instance=context_instance)

def request_ride(request):
    """Form to request a new ride."""
    data = {'subtitle': 'Request or Create New Ride'}
    return render_to_response('new_ride.html', data,
        RequestContext(request))

def search_rides(request):
    """
    Show rides matching the search criteria of the request.
    """
    context_instance=RequestContext(request)
    
    # Store the valid form in the user's session so new_ride or ride_info can
    # pick it up.
    if request.method == 'POST':
        rr_form = RideRequestForm(request.POST)
        request.session['_search_request'] = request.POST
    elif '_search_request' in request.session:
        rr_form = RideRequestForm(request.session['_search_request'])
    else:
        messages.add_message(request, messages.WARNING,
                             "Please make a search request before you attempt" +
                            " to search")
        return redirect('/')

    if rr_form.is_valid():
        sr = rr_form.save(commit = False)
        sr.user = context_instance['user']
    else:
        return HttpResponse("Unexpected error: form not valid " +
                            str(rr_form.errors), status=500)

    # Set up the template
    data = {}
    data['subtitle'] = 'Search Results'
    data['matching'] = True
    data['rides'] = Ride.get_results_for_searchrequest(sr)
    data['search_request'] = sr

    return render_to_response('rides.html', data, context_instance)

def new_ride(request):
    """
    Page to enter description of new ride, and submit it.
    """

    context_instance = RequestContext(request)

    # A POST request indicates that a DescriptionForm has been submitted.
    if request.method == 'POST':
        rr_form = RideRequestForm(request.session['_search_request'])
        if rr_form.is_valid():
            sr = rr_form.save(commit = False)
            sr.user = context_instance['user']
            sr.submission_time = datetime.now()
        else:
            return HttpResponse("Unexpected error: bad rr_form")

        desc_form = DescriptionForm(request.POST)        
        if desc_form.is_valid():
            ride = Ride()
            ride.description = desc_form.cleaned_data['description']
            ride.save()
            sr.ride = ride
            sr.save()
            messages.add_message(request, messages.SUCCESS, THANK_YOU_MESSAGE)
        else:
            return HttpResponse("Error: Invalid description in form.")

        del request.session['_search_request']
        return redirect('/')

    else:
        return render_to_response('add_description.html',
                                  context_instance)

# Begin Facebook authentication
def facebook_login(request):
    if request.user.is_authenticated():
        return redirect('/')
    else:
        return login(request)

def user_logout(request):
    if request.user.is_authenticated():
        logout(request)
    return render_to_response('home.html', context_instance=RequestContext(request))    

def fb_callback(request):
    response = callback(request)
    return response
    
def facebook_test_login(request, fb_id):
    if request.user.is_authenticated():
        return redirect('/')
    else:
        return test_login(request, fb_id)

# End Facebook authentication
