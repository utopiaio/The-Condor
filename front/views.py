#-*- coding:utf-8 -*-

from front.models import AboutUs, Admissions, ContactUs, Gallery, Home, Messages, Event
from django.shortcuts import render_to_response
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
import re

"""
    RequestContext(request) is used for the STATIC_URL config for the template rendering just like the admin
    Add the following in Settings.py

    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.static',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    )

    then when rendering in the template simply use {{ STATIC_URL }} and django will figure out the context and
    serve accordingly
"""

def home (request):
    HOME = Home.objects.all().order_by ("-time_stamp")[:15]
    ABOOOT = AboutUs.objects.all().order_by("-time_stamp")[0]
    ADMISSION = Admissions.objects.all().order_by("-time_stamp")[0]

    # figuring out this part pissed me the FUCK off --- yep one of those blocks where you want to ERASE ERYthing and start all over again -- which i did -- i mean for THIS def
    GALLERY = []
    for i, G in enumerate (Gallery.objects.all()):
        if i == 0:
            GALLERY.append ([G, 0])

        elif i % 4 == 0:
            GALLERY.append ([G, 1])

        else:
            GALLERY.append ([G, 0])

    EVENTS = []
    for i, E in enumerate (Event.objects.filter(display = True)):
        if i == 0:
            EVENTS.append ([E, 0])

        elif i % 3 == 0:
            EVENTS.append ([E, 1])

        else:
            EVENTS.append ([E, 0])

    CONTACT_US = ContactUs.objects.all().order_by("-time_stamp")[0]

    return render_to_response ("index.html", {"HOME": HOME, "ABOOOT": ABOOOT, "ADMISSION": ADMISSION, "EVENTS": EVENTS, "GALLERY": GALLERY, "CONTACT_US": CONTACT_US}, RequestContext(request))

def contact_us (request):
    if not "NAME" in request.POST or not "EMAIL" in request.POST or not "MESSAGE" in request.POST: # making sure the 'user' isn't accessing the freakn url directly -- or something
        return HttpResponseForbidden ("ዴ በላ እን -- እምቢ ስትባል አታውቅም እንዴ --- እንዴዴዴዴዴዴዴዴዴ!")

    # we have all posts -- adding... -- the regx takes like 100ms
    if re.match (r"^[1-9a-zA-Z\._]+@[a-zA-Z]+\.[a-zA-Z]+$", request.POST["EMAIL"]) == None: # NOTE: there is no REAL regx for email -- you just use what you got Mitch!
        return HttpResponse ("0") # EMAIL is crap

    Messages (name = request.POST["NAME"], email = request.POST["EMAIL"], message = request.POST["MESSAGE"], mark_as_read = False).save()
    return HttpResponse ("1") # all is good

def reply (request):
    if not "MESSAGE" in request.POST or not "M_LIST" in request.POST:
        return HttpResponseForbidden ("<title>Code እምቢየው</title><h1 style='font-weight:normal;'>Error: Cannot access this page directly</h1>")

    MESSGES = Messages.objects.filter (id__in = request.POST ["M_LIST"].split("_"))
    MESSGES.update (replied = True)

    EMAIL_LIST = {} # we'll be sending the email using bulk
    ERROR_FLAG = False

    for M in MESSGES: # to be in the freakn messge in the first place -- he/she has to have an email -- so we won't be checking
        EMAIL_LIST [M.email] = "MOE"

    try:
        send_mail(getattr(settings, 'EMAIL_SUBJECT', ''), request.POST["MESSAGE"], getattr(settings, 'EMAIL_FROM', ''), list (EMAIL_LIST), fail_silently = False)
    except:
        messages.add_message (request, messages.ERROR, "Email message has not been sent, Please check your email settings")
        ERROR_FLAG = True

    if not ERROR_FLAG:
            messages.add_message (request, messages.INFO, "Email message has been sent successfully")

        #TODO: log
    return HttpResponseRedirect ("/TheCondor/front/messages/")
