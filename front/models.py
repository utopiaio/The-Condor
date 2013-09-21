from django.db import models
from django.utils.html import format_html

class Home (models.Model):
    """ model for holding home page contents -- basically a stellar powered slider """

    slider_image = models.ImageField (upload_to="static")
    image_title = models.CharField ("Image Title", max_length = 256)
    image_description = models.CharField ("Image Description", max_length = 256)
    time_stamp = models.DateTimeField ("Time Stamp", auto_now=True, auto_now_add=True)

    def __unicode__ (self):
        #return self.image_title.title()
        return u"{}".format (self.image_title)

    def imazion (self):
        """ returns the image -- HTML-ed """

        return format_html ("<img src='/{}' style='max-height:60px; width:auto;' class='img-rounded' />".format (self.slider_image))

    imazion.allow_tags = True

    class Meta:
        verbose_name = "Home"
        verbose_name_plural = "Home"
        ordering = ["image_title", "image_description"]

class AboutUs (models.Model):
    """ About Us Page, only one instace is choosen -- the latest one -- using timestamps """

    about_image = models.ImageField (upload_to="static")
    about_us = models.TextField ("About Us")
    time_stamp = models.DateTimeField ("Time Stamp", auto_now=True, auto_now_add=True)

    def __unicode__ (self):
        if len (self.about_us) < 101:
            return u"{}".format (self.about_us)

        else:
            return u"{}...".format (self.about_us[:100])

    def imazion (self):
        """ returns the image -- HTML-ed """

        return format_html ("<img src='/{}' style='max-height:75px; width:auto;' class='img-rounded' />".format (self.about_image))

    imazion.allow_tags = True

    class Meta:
        verbose_name = "About Us"
        verbose_name_plural = "About Us"
        ordering = ["-time_stamp"]

class Admissions (models.Model):
    """ Admissions, again only the latest is served """

    admissions = models.TextField ("Admissions")
    time_stamp = models.DateTimeField ("Time Stamp", auto_now=True, auto_now_add=True)

    def __unicode__ (self):
        if len (self.admissions) < 101:
            return u"{}".format (self.admissions)

        else:
            return u"{}...".format (self.admissions[:100])

    class Meta:
        verbose_name = "Admission"
        verbose_name_plural = "Admissions"
        ordering = ["-time_stamp"]

class Gallery (models.Model):
    """ Gallery, slider """

    image_description = models.CharField ("Image Description", max_length = 300)
    image = models.ImageField (upload_to = "static")

    def __unicode__ (self):
        #return self.image_description.title()
        if len (self.image_description) < 101:
            return u"{}".format (self.image_description)
        else:
            return u"{}...".format (self.image_description[:100])

    def imazion (self):
        """ returns the image -- HTML-ed """

        return format_html ("<img src='/{}' style='max-height:100px; width:auto;' class='img-rounded' />".format (self.image)) # yep python 2.7.4 is a BAD ASS
        

    imazion.allow_tags = True

    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Gallerias"
        ordering = ["image_description"]

class ContactUs (models.Model):
    """ Contact Us -- again again and again -- only the latest will be served """

    mail_address = models.CharField ("Mail Address", max_length = 256)
    phone = models.CharField ("Phone", max_length = 128)
    email = models.EmailField ("Email")
    iframe = models.TextField ("Google Maps")
    time_stamp = models.DateTimeField ("Time Stamp", auto_now=True, auto_now_add=True)

    def __unicode__ (self):
        #return "Contact Us"
        return u"{} --- {} --- {}".format (self.mail_address, self.phone, self.email)

    class Meta:
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us"
        ordering = ["-time_stamp"]

class Event (models.Model):
    """ Coming Up Events """

    title = models.CharField ("Event Title", max_length = 128)
    event = models.TextField ("Event Description")
    image = models.ImageField (upload_to = "static", blank = True)
    event_start = models.DateTimeField ("Event Starts @")
    event_end = models.DateTimeField ("Event Ends @")
    display = models.BooleanField ("Display Event on Site")

    def __unicode__ (self):
        #return self.title.title()
        return u"{}".format (self.title)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["title"]

class Messages (models.Model):
    """ stores messges sent via the Contact Us Page """

    name = models.CharField ("Name", max_length = 256)
    email = models.EmailField ("Email")
    message = models.TextField ("Message")
    sent_on = models.DateTimeField ("Sent On", auto_now=True, auto_now_add=True)
    mark_as_read = models.BooleanField ("Read")
    replied = models.BooleanField ("Replied")

    def __unicode__ (self):
        #return self.name +" "+self.email
        return u"{} - {}".format (self.name, self.email)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["sent_on"]
