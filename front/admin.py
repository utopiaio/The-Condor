from django.contrib import admin, messages
from django.shortcuts import render_to_response
from django.conf.urls import patterns
from django.template.context import RequestContext
from front.models import AboutUs, Admissions, ContactUs, Gallery, Home, Messages, Event
from front.views import reply

class HomeAdmin (admin.ModelAdmin):
    list_display = ["__unicode__", "imazion"]
    list_per_page = 30

class AboutUsAdmin (admin.ModelAdmin):
    list_display = ["__unicode__", "imazion"]
    list_per_page = 30

class ContactUsAdmin (admin.ModelAdmin):
    list_display = ["mail_address", "phone", "email"]
    list_per_page = 30

class GalleryAdmin (admin.ModelAdmin):
    list_display = ["imazion", "__unicode__"]
    list_per_page = 15

class EventAdmin (admin.ModelAdmin):
    list_display = ["title", "event_start", "event_end", "display"]
    actions = ["display_on_site", "remove_from_site"]
    list_per_page = 30

    def display_on_site (self, request, queryset):
        queryset.update (display = True)
        messages.add_message (request, messages.INFO, "Selected events will now be displayed on site.")

    def remove_from_site (self, request, queryset):
        queryset.update (display = False)
        messages.add_message (request, messages.INFO, "Selected events are removed from the site.")

    display_on_site.short_description = "Display on Site"
    remove_from_site.short_description = "Hide Event"

class MessgeAdmin (admin.ModelAdmin):
    list_display = ["name", "email", "sent_on", "mark_as_read", "replied"]
    actions = ["reply"]
    list_per_page = 30

    def reply (self, request, queryset):
        M_LIST = []
        for M in queryset:
            M_LIST.append (M.id)

        return render_to_response ("reply.html", {"M_LIST": M_LIST}, RequestContext(request))

    reply.short_description = "Reply"

    def get_urls (self):
        urls = super (MessgeAdmin, self).get_urls()
        REPLY = patterns ('',(r'^reply/$', self.admin_site.admin_view (reply, cacheable=False)))
        return REPLY + urls

admin.site.register (AboutUs, AboutUsAdmin)
admin.site.register (Admissions)
admin.site.register (ContactUs, ContactUsAdmin)
admin.site.register (Event, EventAdmin)
admin.site.register (Gallery, GalleryAdmin)
admin.site.register (Home, HomeAdmin)
admin.site.register (Messages, MessgeAdmin)
