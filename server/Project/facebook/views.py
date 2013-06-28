import urllib

from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse


def login(request):
    """ First step of process, redirects user to facebook, which redirects
    to authentication_callback. """
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': settings.FACEBOOK_SCOPE,
        'redirect_uri': request.build_absolute_uri(reverse('facebook-callback')),
    }
    # return HttpResponseRedirect('https://www.facebook.com/dialog/oauth?'
    #                                                 + urllib.urlencode(args))
    return HttpResponseRedirect('https://m.facebook.com/dialog/oauth?'
                                + urllib.urlencode(args))


def callback(request):
    """ Second step of the login process.
    It reads in a code from Facebook, then redirects back to the home page. """
    code = request.GET.get('code')
    user = authenticate(token=code, request=request)

    if user.is_anonymous():
        #we have to set this user up
        url = reverse('facebook_setup')
        url += "?code=%s" % code
        resp = HttpResponseRedirect(url)
    else:
        auth_login(request, user)
        #figure out where to go after setup
        url = getattr(settings, "LOGIN_REDIRECT_URL", "/")
        resp = HttpResponseRedirect(url)

    return resp
    
def test_login(request, fb_id):
    from facebook.models import FacebookProfile

    try:
        fb_user = FacebookProfile.objects.get(facebook_id=fb_id)
        user = fb_user.user
    except FacebookProfile.DoesNotExist:
        user = User.objects.create_user(fb_profile['id'],
                                        fb_profile['email'])
        user.first_name = fb_profile['first_name']
        user.last_name = fb_profile['last_name']

        # Facebook allows for longer name. This fixes the inconsistencies between
        # Django and Postgres
        if len(user.first_name) > 30:
            user.first_name = user.first_name[:30]
        if len(user.last_name ) > 30:
            user.last_name = user.last_name[:30]

                # with django-primate User has one field called 'name' instead
                # of first_name and last_name
        user.name = u'%s %s' % (user.first_name, user.last_name)
        user.save()
        
        # Create the FacebookProfile
        fb_user = FacebookProfile(user=user,
                                  facebook_id=fb_profile['id'],
                                  access_token=access_token)
        fb_user.save()

    fb_user.user.backend = 'django.contrib.auth.backends.ModelBackend' 
    auth_login(request, fb_user.user)
    url = getattr(settings, "LOGIN_REDIRECT_URL", "/")
    resp = HttpResponseRedirect(url)
    return resp
