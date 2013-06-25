#-*- coding: utf-8 -*-

from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.conf.urls import patterns
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from condor.models import Attendance, ClassRoom, GradeReport, Level, Parent, Student, Subject, AcademicCalendar, Config
from condor.views import grade_report, generate_report_card, send_message, notify_parents, student_transfer, send_message_p

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter

class ClassLevelFilter (SimpleListFilter):
    """
        Teacher Teaching permission
        codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
        name:     {Level.grade}-{ClassRoom.section}: {Subject.name}

        Teacher Head Permission
        codename: H_{Level.grade}_{ClassRoom.section}
        name:     Head Teacher of {Level.grade}-{ClassRoom.section}
    """

    title = _('Level')
    parameter_name = 'class_level'

    def lookups (self, request, model_admin):
        RETURNX = []

        if request.user.is_superuser:
            for LEVEL in Level.objects.all():
                RETURNX.append ((LEVEL, _(str (LEVEL))))

        else:
            # The user should be able to see the students where he/she teaches and where he/she is head of
            LEVEL_LIST = []         # will be used to ensure the permission we are checking is associated with a class room
            LEVEL_LIST_RETURNX = {} # holds list of level list where the user is authorized to WATCH the students under

            for L in Level.objects.all():
                LEVEL_LIST.append (u""+ str(L))

            for P in request.user.user_permissions.all():   # this will return 'our' permissions
                if P.codename[0] == "H":                    # the permission is associated with the user -- the teacher -- being a head of a class room
                    LEVEL_LIST_RETURNX [P.codename.split("_")[1]] = "MOE"

                elif P.codename.split ("_")[0] in LEVEL_LIST:
                    LEVEL_LIST_RETURNX [P.codename.split("_")[0]] = "MOE"

            for L in list (LEVEL_LIST_RETURNX):
                RETURNX.append ((L, _(L)))

        return RETURNX

    def queryset (self, request, queryset):
        if "student/" in request.path: # The filter is being used inside the student model
            if self.value():
                return queryset.filter (class_room__grade__grade = self.value())

        elif "gradereport/" in request.path:
            if self.value():
                return queryset.filter (student__class_room__grade__grade = self.value())

        elif "classroom/" in request.path:
            if self.value():
                return queryset.filter (grade__grade = self.value())

class ClassSectionFilter (SimpleListFilter):
    title = _('Section')
    parameter_name = 'class_section'

    def lookups (self, request, model_admin):
        RETURNX = []
        SECTION_LIST = {}

        if request.user.is_superuser:
            for CR in ClassRoom.objects.all():
                SECTION_LIST [CR.section] = "MOE"

            for SECTION in list(sorted (SECTION_LIST)):
                RETURNX.append ((SECTION, _(SECTION)))

        else:
            LEVEL_LIST = []

            for L in Level.objects.all():
                LEVEL_LIST.append (u""+ str(L))

            for P in request.user.user_permissions.all():       # this will return 'our' permissions
                if P.codename[0] == "H":                        # the permission is associated with the user -- the teacher -- being a head of a class room
                    SECTION_LIST [P.codename.split("_")[2]] = "MOE"

                elif P.codename.split ("_")[0] in LEVEL_LIST:   # making sure our permission is our permission associated with teaching
                    SECTION_LIST [P.codename.split("_")[1]] = "MOE"

            for SECTION in list(sorted (SECTION_LIST)):
                RETURNX.append ((SECTION, _(SECTION)))

        return RETURNX

    def queryset(self, request, queryset):
        if "student/" in request.path: # The filter is being used inside the student model
            if self.value():
                return queryset.filter (class_room__section = self.value())

        elif "gradereport/" in request.path:
            if self.value():
                return queryset.filter (student__class_room__section = self.value())

        elif "classroom/" in request.path:
            if self.value():
                return queryset.filter (section = self.value())

class SubjectFilter (SimpleListFilter):
    title = _('Subject')
    parameter_name = 'subject'

    def lookups (self, request, model_admin):
        SUBJECT_LIST = {}
        RETURNX = []
        if request.user.is_superuser: # Show all available subjects
            for S in Subject.objects.all():
                RETURNX.append ((S.name, _(S.name)))

        else:
            SL = []

            for Sub in Subject.objects.all():
                SL.append (u""+ Sub.name)

            for P in request.user.user_permissions.all():
                if len (P.codename.split("_")) == 3:
                    if P.codename.split("_")[2] in SL: # We'll only be concerned with teaching permissions ONLY, head and other permissions are not our concern
                        SUBJECT_LIST [P.codename.split ("_")[2]] = "MOE"

            for S in list (sorted (SUBJECT_LIST)):
                RETURNX.append ((S, _(S)))

        return RETURNX

    def queryset (self, request, queryset):
        if self.value(): # since we're only using it in grade report, we’ll only have one query
            return queryset.filter (subject__name__iexact = self.value())

class ConfigAdmin (admin.ModelAdmin):
    def save_model (self, request, obj, form, change):
        if not change and Config.objects.all().count() == 1: # only one row should exist!
            messages.add_message (request, messages.ERROR, "Seems there is a Report Card Configuration already. Either delete the configuration or edit it. There can't be more than one Report Card Configuration at a time.")
            return

        else:
            obj.save()

class AttendanceAdmin (admin.ModelAdmin):
    filter_horizontal = ["student"]
    list_display = ["attendance_date", "attendance_type", "academic_semester"]
    readonly_fields = [] # This will be modified dynamically according to the user's permission
    list_filter = ["attendance_date", "attendance_type"]
    actions = ["notify_parents"]
    list_per_page = 30

    def notify_parents (self, request, queryset):
        """ It'll notify student's parent/s aboot their son activity, if he or she is in the attendance sheet """

        ATTENDANCE_SHEET = []
        P_COUNT = {} # this will hold a list of unique parents
        for A in queryset:
            ATTENDANCE_SHEET.append (A.id)
            for S in A.student.all():
                for P in S.parents.all():
                    P_COUNT[P.id] = "MOE"

        return render_to_response ("notify_parents.html", {"ATTENDANCE_SHEET": ATTENDANCE_SHEET, "P_COUNT": P_COUNT, "ATTENDANCE": queryset}, RequestContext(request))

    notify_parents.short_description = "Notify Parents"

    def get_actions (self, request):
        actions = super (AttendanceAdmin, self).get_actions(request)

        if not request.user.has_perm ("condor.delete_attendance"):
            if 'delete_selected' in actions:
                del actions ['delete_selected']

        if not request.user.has_perm ("condor.notify_parents_attendance"):
            if 'notify_parents' in actions:
                del actions ['notify_parents']

        return actions

    def change_view (self, request, object_id, form_url='', extra_context=None):
        """ Yep, only super users can edit object details other than the student list...oh ya what are you going to do about it! """

        if not request.user.is_superuser:
            if len (self.readonly_fields) == 0:
                self.readonly_fields = ["attendance_date", "attendance_type", "academic_semester"]

        else: # i think this part is a little buggy, check it!
            self.readonly_fields = []

        return super (AttendanceAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view (self, request, form_url='', extra_context=None):
        """ Changing the read only fields back to the original position """

        self.readonly_fields = []
        return super (AttendanceAdmin, self).add_view (request, form_url, extra_context=extra_context)

    def save_related (self, request, form, formsets, change):
        if not Permission.objects.filter (codename = "notify_parents_attendance").exists():
            # Creating a permission, that allows a user to notify parents on attendance sheet...what-what
            NEW_P = Permission()
            NEW_P.codename = "notify_parents_attendance"
            NEW_P.name = "Can Notify Parents (on Attendance)"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="attendance")
            NEW_P.save()

        if not change:
            """
                - a new attendance object is being added, we will have to check for collision in the attendance sheet before saving the students in the requested list
                - We don't have to check whether or not the user has removed a student which he/she isn't supposed to, we only check the added one and check em'
                - we also have to make sure that the user [i.e. the teacher] is authenticated to do what he/she did
            """

            # Step Uno: Checking for double dip ---------------------------------------------------------------------------------------------------------------------------------------------------
            DOBULE_DIP = []
            for A in Attendance.objects.filter (academic_semester__id__exact = request.POST['academic_semester'], attendance_date__exact=request.POST['attendance_date']):
                for S in A.student.all():
                    DOBULE_DIP.append (S.id)

            for S in request.POST.getlist ('student'):
                if int (S) in DOBULE_DIP: # Collision detected!, add a message and return without saving the related object of students
                    messages.add_message (request, messages.ERROR, "Collision has been detected; the student(s) you have selected already exist in another attendance sheet. The student(s) you've selected was/were not added to the attendance sheet")
                    return

            # if it didn't return, that means we can go to step dos...well what are we waiting for; Let's get to it........that was SOO GAY!
            # Step Dos: Checking user permission --------------------------------------------------------------------------------------------------------------------------------------------------
            PERMISSION_LIST = [] # It'll hold all the permission that a user must have in order for the request to be valid one
            for S in Student.objects.filter (id__in = request.POST.getlist ("student")):
                PERMISSION_LIST.append (u"condor.H_"+ S.class_room.grade.grade +"_"+ S.class_room.section) # Adding head of teacher permission

            if not request.user.has_perms (PERMISSION_LIST): # MOT...drum roll, The user doesn't have permission to do what he did
                messages.add_message (request, messages.ERROR, "Permission denied, your request has not been saved because you do not have the necessary permission")
                return

            form.save() # The user is a legit one, so your wish is my command or is it...

        elif change: # Object is being edited, now things might get messy but is doable...doable [funny]
            PREVIOUS_ATTENDANCE = Attendance.objects.get (id = request.META['HTTP_REFERER'][request.META['HTTP_REFERER'].rfind('/', 0, -1) + 1: -1]) # we know this exists
            PREVIOUS_LIST = [] #  Holds list of student id's who were in the previous attendance state

            for S in PREVIOUS_ATTENDANCE.student.all():
                PREVIOUS_LIST.append (u""+ str(S.id)) # Since get list in request returns a list containing id's as UNICODE: we have to cast to that one in order to compare

            # Step Uno: Checking for double dip ---------------------------------------------------------------------------------------------------------------------------------------------------
            DOBULE_DIP = []
            if request.user.is_superuser: # Only super users are allowed to change details of an already existing attendance object, yall feell me...WEST SIIIIIED!
                for A in Attendance.objects.filter (academic_semester__id__exact = request.POST['academic_semester'], attendance_date__exact=request.POST['attendance_date']).exclude (id = request.META['HTTP_REFERER'][request.META['HTTP_REFERER'].rfind('/', 0, -1) + 1: -1]):
                    for S in A.student.all():
                        DOBULE_DIP.append (S.id)

            else: # If you aren't a super user the only thing you can change is the student list, little MITCH
                for A in Attendance.objects.filter (academic_semester = PREVIOUS_ATTENDANCE.academic_semester, attendance_date = PREVIOUS_ATTENDANCE.attendance_date).exclude (id = request.META['HTTP_REFERER'][request.META['HTTP_REFERER'].rfind('/', 0, -1) + 1: -1]):
                    for S in A.student.all():
                        DOBULE_DIP.append (S.id)

            for S in request.POST.getlist ('student'):
                if int (S) in DOBULE_DIP:
                    messages.add_message (request, messages.ERROR, "Collision has been detected; the student(s) you have selected already exist in another attendance sheet. The student(s) you've selected was/were not added to the attendance sheet")
                    return

            # Step Dos: Checking user permission --------------------------------------------------------------------------------------------------------------------------------------------------
            PERMISSION_LIST = [] # Here permission list will be built a little differently; it'll hold permission for adding and removing a student from the list
            for S in request.POST.getlist ("student"): # Looping through the requested student id list, Added Student
                if S not in PREVIOUS_LIST:
                    PERMISSION_LIST.append (u"condor.H_"+ Student.objects.get (pk = S).class_room.grade.grade +"_"+ Student.objects.get (pk = S).class_room.section)

            for S in PREVIOUS_LIST: # removed Student
                if S not in request.POST.getlist ("student"):
                    PERMISSION_LIST.append (u"condor.H_"+ Student.objects.get (pk = S).class_room.grade.grade +"_"+ Student.objects.get (pk = S).class_room.section)

            if not request.user.has_perms (PERMISSION_LIST):
                messages.add_message (request, messages.ERROR, "Permission denied, your request has not been saved because you do not have the necessary permission")
                return

            form.save()

    def get_urls (self):
        urls = super (AttendanceAdmin, self).get_urls()
        NOTIFY_PARENTS = patterns ('',(r'^notify_parents/$', self.admin_site.admin_view (notify_parents, cacheable=False)))
        return NOTIFY_PARENTS + urls

class AcademicCalendarAdmin (admin.ModelAdmin):
    list_display = ["semester", "academic_year", "semester_status"]
    list_filter = ["academic_year", "semester", "semester_status"]
    list_per_page = 30

class ClassRoomAdmin (admin.ModelAdmin):
    list_filter = [ClassSectionFilter, ClassLevelFilter]
    list_display = ["grade", "section", "student_count"]
    list_display_links = ["grade"]
    actions = ["generate_report_card"]
    list_per_page = 40

    def queryset (self, request):
        if not request.user.is_superuser:
            self.list_display_links[0] = None # Only super user can edit a class room information; so we are setting 'list_display_links' to None if the user is no a super one

            CLASS_LIST = []
            for CR in super (ClassRoomAdmin, self).queryset(request):
                if request.user.has_perm ("condor.H_"+ CR.grade.grade +"_"+ CR.section):
                    CLASS_LIST.append (CR.id)

            return ClassRoom.objects.filter (id__in = CLASS_LIST).order_by ("grade", "section")

        else:
            self.list_display_links[0] = "grade"
            return super (ClassRoomAdmin, self).queryset(request).order_by ("grade", "section")

    def change_view (self, request, object_id, form_url='', extra_context=None):
        if not request.user.is_superuser:
            return HttpResponseForbidden ("<title>Code እምቢየው</title><h1 style='font-weight:normal;'>Permission denied, only superusers are allowed to change Class Room information</h1>")

        return super(ClassRoomAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def generate_report_card (self, request, queryset):
        """ Well...it generates a report card on the selected class room """
        # scan classrooms and subject's associated with it and check all is in order

        CLASS_ROOM = []     # sending selected class rooms
        for CR in queryset:
            CLASS_ROOM.append ([CR, CR.student_count()])

        #return render_to_response ("generate_report_card.html", {"CLASS_ROOM": CLASS_ROOM, "ACADEMIC_CALENDAR": AcademicCalendar.objects.filter (academic_year = AcademicCalendar.objects.filter(semester_status = True)[0].academic_year).order_by ("semester", "academic_year")}, RequestContext(request))
        return render_to_response ("generate_report_card.html", {"CLASS_ROOM": CLASS_ROOM, "ACADEMIC_CALENDAR": AcademicCalendar.objects.filter (semester_status = True).order_by ("semester", "academic_year")}, RequestContext(request))

    generate_report_card.short_description = "Generate Report Card"

    def get_actions (self, request):
        actions = super (ClassRoomAdmin, self).get_actions(request)

        if not request.user.has_perm ("condor.generate_report_card"):
            del actions ['generate_report_card']

        if not request.user.has_perm ("condor.delete_classroom"):
            del actions ['delete_selected']

        return actions

    def get_urls (self):
        """ attaching our URL to the admin site, i.e. NO cache and seamless integration """

        urls = super (ClassRoomAdmin, self).get_urls()
        GENERATE_REPORT_CARD = patterns ('',(r'^generate_report_card/$', self.admin_site.admin_view (generate_report_card, cacheable=False)))
        return GENERATE_REPORT_CARD + urls

class SubjectAdmin (admin.ModelAdmin):
    list_display = ["name", "name_a", "given_in_semister_only", "use_letter_grading"]
    list_per_page = 40

class GradeReportAdmin (admin.ModelAdmin):
    list_filter = ["academic_calendar__academic_year", "academic_calendar__semester", ClassLevelFilter, ClassSectionFilter, SubjectFilter]
    search_fields = ["student__first_name", "student__father_name", "student__gf_name", "subject__name", "student__class_room__section", "student__class_room__grade__grade"]
    list_display = ["student", "academic_calendar", "subject", "mark"]
    ordering = ["subject__name", "academic_calendar", "student__first_name", "student__first_name", "student__gf_name"]
    list_per_page = 100

    def formfield_for_foreignkey (self, db_field, request, **kwargs):
        if db_field.name == "student" and not request.user.is_superuser:
            SUBJECT_LIST = []
            for S in Subject.objects.all():
                SUBJECT_LIST.append (S.name)

            FK_STUDENT_LIST = []
            for P in request.user.user_permissions.all():
                if P.codename[P.codename.rfind("_") + 1:] in SUBJECT_LIST:
                    for S in Student.objects.filter (class_room__grade__grade = P.codename.split("_")[0], class_room__section = P.codename.split("_")[1]):
                        FK_STUDENT_LIST.append (S.id)

            kwargs["queryset"] = Student.objects.filter(id__in = FK_STUDENT_LIST)

        if db_field.name == "subject" and not request.user.is_superuser:
            SUBJECT_LIST = []
            for S in Subject.objects.all():
                SUBJECT_LIST.append (S.name)

            FK_SUBJECT_LIST = []
            for P in request.user.user_permissions.all():
                if P.codename[P.codename.rfind("_") + 1:] in SUBJECT_LIST:
                    FK_SUBJECT_LIST.append (P.codename[P.codename.rfind("_") + 1:])
                    
            kwargs["queryset"] = Subject.objects.filter(name__in = FK_SUBJECT_LIST)

        return super (GradeReportAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def queryset (self, request):
        if not request.user.is_superuser:
            SUBJECT_LIST = [] # Will be used to identify "our" permissions, ya naha wa i mean...what son am a NEEGA and you're not!
            for S in Subject.objects.all():
                SUBJECT_LIST.append (S.name)

            GRADE_REPORT_LIST = [] # holds student id list which should be returned...the user has the permission to do so
            for P in request.user.user_permissions.all():
                if P.codename[P.codename.rfind("_") + 1:] in SUBJECT_LIST: # it's our permission, split by _ then get: GRADE > SECTION > SUBJECT
                    # codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
                    for GR in GradeReport.objects.filter (student__class_room__grade__grade = P.codename.split("_")[0], student__class_room__section = P.codename.split("_")[1], subject__name = P.codename.split("_")[2]):
                        GRADE_REPORT_LIST.append (GR.id)

            return GradeReport.objects.filter (id__in = GRADE_REPORT_LIST)

        else:
            return super (GradeReportAdmin, self).queryset(request)

    def save_model (self, request, obj, form, change):
        """ Hey Hey Hey...let me see your id...or your boobs-your choice...i prefer the BOOBS unless you're OVER 18...EEEWWWWWWW """

        if not request.user.is_superuser:
            if not request.user.has_perm ("condor."+ Student.objects.get (pk = request.POST["student"]).class_room.grade.grade +"_"+ Student.objects.get (pk = request.POST["student"]).class_room.section +"_"+ Subject.objects.get (pk = request.POST ["subject"]).name):
                messages.add_message (request, messages.ERROR, "Denied, the request you've made has content you are not authorized to add/edit. Your request has not been saved")
                return None

            elif request.user.has_perm ("condor."+ Student.objects.get (pk = request.POST["student"]).class_room.grade.grade +"_"+ Student.objects.get (pk = request.POST["student"]).class_room.section +"_"+ Subject.objects.get (pk = request.POST ["subject"]).name):
                if not Permission.objects.filter (codename = "generate_report_card").exists():
                    NEW_P = Permission ()
                    NEW_P.codename = "generate_report_card"
                    NEW_P.name = "Can Generate Report Card"
                    NEW_P.content_type = ContentType.objects.get (app_label="condor", model="gradereport")
                    NEW_P.save()

                obj.save()

        elif request.user.is_superuser:
            if not Permission.objects.filter (codename = "generate_report_card").exists():
                NEW_P = Permission ()
                NEW_P.codename = "generate_report_card"
                NEW_P.name = "Can Generate Report Card"
                NEW_P.content_type = ContentType.objects.get (app_label="condor", model="gradereport")
                NEW_P.save()

            """ we are going have to check whether or not the super user has made the right choices...i feel OLD...which takes like two lines """
            if obj.subject not in obj.student.class_room.grade.subject.all():
                messages.add_message (request, messages.ERROR, "Error: the subject you have selected is not given in the specified grade level, No changes have been made.")
                return None

            obj.save()

class LevelAdmin (admin.ModelAdmin):
    filter_horizontal = ["subject"]
    list_display = ["grade", "subject_count"]
    list_filter = ["grade"]
    list_per_page = 50

    def save_related (self, request, form, formsets, change):
        if change:
            # If any grade change occurred; the save override will take care of the removal of previous permissions associated with the previous grade
            # All we have to care aboot here is saving the related objects i.e. subject with the appropriate permissions

            # codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
            # name:     {Level.grade}-{ClassRoom.section}: {Subject.name}

            LEVEL = Level.objects.get (pk = request.META['HTTP_REFERER'][request.META['HTTP_REFERER'].rfind('/', 0, -1) + 1: -1]) # level object: related fields UNSAVED untill form save
            if LEVEL.classroom_set.count(): # we will have to create/edit permission if a level is associated with a class room
                NEW_SUBJECT_LIST = []
                for SID in request.POST.getlist ("subject"): # Looping through the subject id's
                    NEW_SUBJECT_LIST.append (Subject.objects.get(pk = SID).name)

                for CR in LEVEL.classroom_set.all(): # After finishing this loop we would have deleted any permission that shouldn't exist anymore due to the change in the level object 
                    for S in LEVEL.subject.all():
                        if S.name not in NEW_SUBJECT_LIST:
                            Permission.objects.filter (codename = LEVEL.grade +"_"+ CR.section +"_"+ S.name).delete()

                for CR in LEVEL.classroom_set.all(): # After finishing this loop we would have created any new permission that should be created due to the change in the level object 
                    for S in NEW_SUBJECT_LIST:
                        if not Permission.objects.filter (codename = LEVEL.grade +"_"+ CR.section +"_"+ S).exists():
                            # Permission Structure
                            # codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
                            # name:     {Level.grade}-{ClassRoom.section}: {Subject.name}
                            NEW_P = Permission ()
                            NEW_P.codename = LEVEL.grade +"_"+ CR.section +"_"+ S
                            NEW_P.name = LEVEL.grade +"-"+ CR.section +": "+ S
                            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
                            NEW_P.save()

        form.save()

class ParentAdmin (admin.ModelAdmin):
    list_display = ["__unicode__", "email", "phone_number"]
    list_display_links = ["__unicode__",]
    actions = ["send_message_p"]
    list_per_page = 50

    def queryset (self, request):
        if not request.user.is_superuser:
            self.list_display_links[0] = None # Only super user can edit a student's information; so we are setting 'list_display_links' to None if the user is no a super one

        else:
            self.list_display_links [0] = "__unicode__" # Well it's the master, so set it back again IF it wasn't set before

        return super (ParentAdmin, self).queryset(request)

    def change_view (self, request, object_id, form_url='', extra_context=None):
        """
            - Blocking user if he/she tried to edit a student record, only super users are allowed to do so
            - NOTE: even though change student is given to the user, that will ONLY allow the user to view the objects
        """

        if not request.user.is_superuser:
            return HttpResponseForbidden ("<title>Code እምቢየው</title><h1 style='font-weight:normal;'>Permission denied, only superusers are allowed to change student's information</h1>")

        return super(ParentAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def get_actions (self, request):
        actions = super (ParentAdmin, self).get_actions(request)

        if not request.user.has_perm ("condor.send_message_p"):
            del actions ['send_message_p']

        if not request.user.has_perm ("condor.delete_parent"):
            del actions ['delete_selected']

        return actions

    def send_message_p (self, request, queryset):
        P_LIST = []
        for P in queryset:
            P_LIST.append (P.id)

        return render_to_response ("send_message_d.html", {"P_LIST": P_LIST}, RequestContext(request))

    send_message_p.short_description = "Send Message to Parents"

    def get_urls (self):
        urls = super (ParentAdmin, self).get_urls()
        PARENTS_SD = patterns ('',(r'^send_message_p/$', self.admin_site.admin_view (send_message_p)))
        return PARENTS_SD + urls

class StudentAdmin (admin.ModelAdmin):
    list_display = ["first_name", "father_name", "gf_name", "class_room", "contact_info"]
    list_display_links = ["first_name",]
    list_filter = [ClassLevelFilter, ClassSectionFilter]
    filter_horizontal = ["parents"]
    search_fields = ["first_name", "father_name", "gf_name", "class_room__section", "class_room__grade__grade"]
    actions = ["send_message", "grade_report", "transfer_student"]
    list_per_page = 40

    def send_message (self, request, queryset):
        """ send a custom message to selected sutdent(s) parent(s), must have permission to access this action """

        STUDENTS = {} # Holds id of students (unique)
        PARENTS = {} # Holds id of parents (unique)

        for student in queryset:
            STUDENTS [student.id] = "MOE"
            STUDENT_PARENTS = student.parents.all()
            for PARENT in STUDENT_PARENTS:
                PARENTS [PARENT.id] = "MOE"

        return render_to_response ("send_message.html", {"STUDENTS": STUDENTS, "PARENTS": PARENTS}, RequestContext(request))

    def transfer_student (self, request, queryset):
        """ accepts list of students and transfers them the a specified class room """

        # NOTE: we are going to transfer one class room at a time, in order to avoid a messy checking up at the end...what if...Magan Fox 16 came and GRABBED you by the nuts...O--M--G!
        # NOTE: can't use DISTINCT, not supported on SQLite
        CLASS_VERIFIER = {}
        for S in queryset:
            CLASS_VERIFIER [S.class_room] = S.class_room.id
            EXCLUDE_ID = S.class_room.id

        if len(CLASS_VERIFIER) == 1: # All the students reside on a single class room, so we should be able to transfer students without crying about it
            return render_to_response ("student_transfer.html", {"STUDENTS": queryset.order_by ("first_name", "father_name", "gf_name"), "CLASS_ROOM": queryset[0].class_room, "TRANSFERABLE_CLASSES": ClassRoom.objects.all().exclude (id = EXCLUDE_ID).order_by ("grade__grade", "section")}, RequestContext(request))

        else:
            messages.add_message (request, messages.ERROR, "Transfer operations can only be done on one class at a time. Make sure the students you have selected attend the same class room. (Tip: Luke use the...Filters)")

    def grade_report (self, request, queryset):
        """ Redirects to an easy to use template by which the teacher can submit a grade report """

        # TODO:...you know who i like to DO...Megan Fox 16: Under which class is which subject is given, collision detection, the whole shebang-abang
        # NOTE: The selected students are the only ones that the user can view so, do little permission check

        # TIP: Do Class - Subject combo thingi
        SCROLL_SPY = {} # It will hold class with subject combo thingi, will also be a scroll spy, Bootstrap the shit out of it

        SUBJECT_LIST = []
        for S in Subject.objects.all():
            SUBJECT_LIST.append (S.name)

        if request.user.is_superuser: # for some reson request.user.user_permissions.all() does not return all the permission set when the user is a su
            PERMISSION_FILTER = Permission.objects.all()
        else:
            PERMISSION_FILTER = request.user.user_permissions.all()

        for P in PERMISSION_FILTER: # Using the our permission list we can have the class, section and grade – now that's flexibility - MITCH!
            if P.codename[P.codename.rfind("_") + 1:] in SUBJECT_LIST: # it's our permission, split by _ then get: GRADE > SECTION > SUBJECT
                SCROLL_SPY [P.codename.split("_")[0] +"_"+ P.codename.split("_")[1] +"_"+ P.codename.split("_")[2].replace (" ", "X")] = queryset.filter (class_room__grade__grade = P.codename.split("_")[0], class_room__section = P.codename.split("_")[1])

        SCROLL_LIST = []
        for SP in sorted (SCROLL_SPY):
            if SCROLL_SPY[SP]:
                SCROLL_LIST.append ([SP, SCROLL_SPY [SP]])

        return render_to_response ("submit_grade_report.html", {"USER": request.user, "SCROLL_LIST": SCROLL_LIST, "SEMISTER": AcademicCalendar.objects.filter (semester_status = True)}, RequestContext (request))

    send_message.short_description = "Send Message to Parents"
    grade_report.short_description = "Submit Grade Report"
    transfer_student.short_description = "Transfer Students"

    def queryset (self, request):
        if not request.user.is_superuser:
            self.list_display_links[0] = None # Only super user can edit a student's information; so we are setting 'list_display_links' to None if the user is no a super one

            SUBJECT_LIST = [] # Will be used to identify "our" permissions, ya naha wa i mean...what son am a NEEGA; are you?
            for S in Subject.objects.all():
                SUBJECT_LIST.append (S.name)

            STUDENT_LIST = [] # holds student id list which should be returned...the user has the permission to do so
            for P in request.user.user_permissions.all():
                if P.codename[P.codename.rfind("_") + 1:] in SUBJECT_LIST: # it's our permission, split by _ then get: GRADE > SECTION > SUBJECT
                    for S in Student.objects.filter (class_room__grade__grade = P.codename.split("_")[0], class_room__section = P.codename.split("_")[1]):
                        STUDENT_LIST.append (S.id)

            return Student.objects.filter(id__in = STUDENT_LIST).order_by ("class_room__grade__grade", "class_room__section", "first_name", "father_name", "gf_name") # At last returning students found in class where the user teaches

        else:
            self.list_display_links [0] = "first_name" # Well it's the master, so set it back again IF it wasn't set before
            return super (StudentAdmin, self).queryset(request).order_by ("class_room__grade__grade", "class_room__section", "first_name", "father_name", "gf_name")

    def change_view (self, request, object_id, form_url='', extra_context=None):
        """
            - Blocking user if he/she tried to edit a student record, only super users are allowed to do so
            - NOTE: even though change student is given to the user, that will ONLY allow the user to view the objects
        """

        if not request.user.is_superuser:
            return HttpResponseForbidden ("<title>Code እምቢየው</title><h1 style='font-weight:normal;'>Permission denied, only superusers are allowed to change student's information</h1>")

        return super(StudentAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls (self):
        urls = super (StudentAdmin, self).get_urls()
        SEND_MESSAGE = patterns ('',(r'^send_message/$', self.admin_site.admin_view (send_message)))
        GRADE_REPORT = patterns ('',(r'^grade_report/$', self.admin_site.admin_view (grade_report)))
        STUDENT_TRANSFER = patterns ('',(r'^student_transfer/$', self.admin_site.admin_view (student_transfer)))
        return SEND_MESSAGE + GRADE_REPORT + STUDENT_TRANSFER + urls

    def get_actions (self, request):
        actions = super (StudentAdmin, self).get_actions(request)

        if not request.user.has_perm ("condor.send_message"):
            del actions ['send_message']

        if not request.user.has_perm ("condor.delete_student"):
            del actions ['delete_selected']

        if not request.user.has_perm ("condor.grade_report"):
            del actions ['grade_report']

        if not request.user.has_perm ("condor.transfer_student"):
            del actions ['transfer_student']

        return actions

admin.site.register (Attendance, AttendanceAdmin)
admin.site.register (ClassRoom, ClassRoomAdmin)
admin.site.register (GradeReport, GradeReportAdmin)
admin.site.register (Level, LevelAdmin)
admin.site.register (Parent, ParentAdmin)
admin.site.register (Student, StudentAdmin)
admin.site.register (Subject, SubjectAdmin)
admin.site.register (AcademicCalendar, AcademicCalendarAdmin)
admin.site.register (Config, ConfigAdmin)

#admin.site.register (Permission)
