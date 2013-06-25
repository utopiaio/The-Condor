#-*- coding: utf-8 -*-

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete
from django.utils.html import format_html
import re

"""
    TODO: make 'front' App
        - off the god damn chain front-end for st. Joseph school
"""

def validate_mark (value):
    """ Validates mark passed is not a negative number or greater than 200 """

    if value < 0:
        raise ValidationError (u"Mark cannot be a negative number")

    elif value > 200:
        raise ValidationError (u"A mark cannot be greater than 200")

def validate_year (value):
    """ Validates year passed is a legit one """

    if re.match (r"^[1-9]{1}[0-9]{3}([/]{1}[0-9]{2})?$", value) == None:
        raise ValidationError (u"Format not supported. Use YYYY or YYYY/DD")

def pre_delete_cleaner (sender, **kwargs):
    """ This signal listener will remove any associated permissions affiliated with the object which is aboooot to be deleted """

    """
        Teacher Teaching permission
        codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
        name:     {Level.grade}-{ClassRoom.section}: {Subject.name}

        Teacher Head Permission
        codename: H_{Level.grade}_{ClassRoom.section}
        name:     Head Teacher of {Level.grade}-{ClassRoom.section}
    """

    if "Level" in str (type (kwargs["instance"])):
        if kwargs["instance"].classroom_set.count (): # The object about to be deleted is affiliated with a class room, permission removal is necessary
            for CR in kwargs["instance"].classroom_set.all():
                Permission.objects.filter (codename__istartswith = kwargs["instance"].grade +"_"+ CR.section).delete()

    elif "Subject" in str (type (kwargs["instance"])):
        Permission.objects.filter (codename__iendswith = "_"+ kwargs["instance"].name).delete()

    elif "ClassRoom" in str (type (kwargs["instance"])):
        Permission.objects.filter (codename__istartswith = kwargs["instance"].grade.grade +"_"+ kwargs["instance"].section).delete()
        Permission.objects.get (codename = u"H_" + kwargs["instance"].grade.grade +"_"+ kwargs["instance"].section).delete()

class Config (models.Model):
    """ Holds configuration variables for the report card """

    def clean (self):
        self.head_master = self.head_master.title()

    head_master = models.CharField ("Headmaster", max_length=256)
    promotion_min = models.DecimalField ("Promotion Average", max_digits=5, decimal_places=2)
    max_absent_count = models.IntegerField ("Max Absent")
    max_late_count = models.IntegerField ("Max Late")

    def __unicode__ (self):
        #return u""+ self.school_name + " Report Card Settings"
        return u"{}".format (self.head_master)

    class Meta:
        verbose_name = "Report Card Configuration"
        verbose_name_plural = "Report Card Configuration"

class Student (models.Model):
    """ Holds Student's Information """

    first_name = models.CharField ("First Name", max_length=75)
    father_name = models.CharField ("Father Name", max_length=75)
    gf_name = models.CharField ("Grandfather Name", max_length=75)
    parents = models.ManyToManyField ("Parent")
    class_room = models.ForeignKey ("ClassRoom")

    def __unicode__(self):
        return u"{} {} {} @ {}".format (self.first_name, self.father_name, self.gf_name, self.class_room)

    def clean (self):
        """ Simply capitalizing the first letter before saving, guess what...it works on UNICODE too, by doing nothing! """

        self.first_name = self.first_name.title()
        self.father_name = self.father_name.title()
        self.gf_name = self.gf_name.title()

    def save (self, *args, **kwargs):
        super (Student, self).save(*args, **kwargs)

        # Creating permissions which allows the super user to assign privileges on users
        if not Permission.objects.filter (codename = "send_message").exists():
            NEW_P = Permission ()
            NEW_P.codename = "send_message"
            NEW_P.name = "Can Send Messages to Parents"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="student")
            NEW_P.save()

        if not Permission.objects.filter (codename = "grade_report").exists():
            NEW_P = Permission ()
            NEW_P.codename = "grade_report"
            NEW_P.name = "Can Submit Grade Report"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="student")
            NEW_P.save()

        if not Permission.objects.filter (codename = "transfer_student").exists():
            NEW_P = Permission ()
            NEW_P.codename = "transfer_student"
            NEW_P.name = "Can Transfer Student"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="student")
            NEW_P.save()

    def contact_info (self):
        """ Minor tweaking is done in the index page son, to initiate the tooltips """

        P_ICON = "";
        for P in self.parents.all():
            P_ICON += "<i data-toggle='tooltip' data-original-title='"+ P.first_name +" "+ P.father_name +"</br>"+ P.phone_number +"' class='icon icon-user TOOLTIPX' style='margin-right:3px;'></i>"

        return format_html (P_ICON)

    contact_info.allow_tags = True

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        unique_together = (("first_name", "father_name", "gf_name", "class_room"),)

class Parent (models.Model):
    """ Holds Parent's Information """

    first_name = models.CharField ("First Name", max_length=75)
    father_name = models.CharField ("Father Name", max_length=75)
    phone_number = models.CharField ("Mobile Number", max_length=75, unique=True)
    email = models.EmailField ("Email Address", max_length=255, blank=True)

    def __unicode__ (self):
        #return u""+ self.first_name + " " + self.father_name
        return u"{} {}".format (self.first_name, self.father_name)

    def save (self, *args, **kwargs):
        self.first_name = self.first_name.title()
        self.father_name = self.father_name.title()
        super (Parent, self).save(*args, **kwargs)

        if not Permission.objects.filter (codename = "send_message_p").exists():
            NEW_P = Permission ()
            NEW_P.codename = "send_message_p"
            NEW_P.name = "Can Send Messages to Parents (Directly)"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="parent")
            NEW_P.save()

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
        ordering = ["first_name"]

class AcademicCalendar (models.Model):
    """ This model controls how grades are computed """

    SEMESTER_LIST = (("P_I", "Period I"), ("P_II", "Period II"), ("S_I", "Semester I"), ("P_III", "Period III"), ("P_IV", "Period IV"), ("S_II", "Semester II"))
    semester = models.CharField ("Semester", max_length=5, choices=SEMESTER_LIST)
    academic_year = models.CharField ("Academic Year", max_length = 7, validators=[validate_year])
    semester_status = models.BooleanField ("Semester Status")

    def __unicode__ (self):
        if self.semester[0] == "P":
            #return u"Period "+ self.semester.split("_")[1] +" of "+ str(self.academic_year)
            return u"Period {} of {}".format (self.semester.split("_")[1], self.academic_year)

        else:
            #return u"Semester "+ self.semester.split("_")[1] +" of "+ str(self.academic_year)
            return u"Semester {} of {}".format (self.semester.split("_")[1], self.academic_year)
            

    class Meta:
        verbose_name = "Academic Calendar"
        verbose_name_plural = "Academic Calendars"
        unique_together = (("semester", "academic_year"),)

class ClassRoom (models.Model):
    """ Holds Class Room Information """

    CLASS_SECTIONS = (("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E"), ("F", "F"), ("G", "G"), ("H", "H"), ("I", "I"), ("J", "J")) # TEN Sections, that's more than enough--Mitch!
    section = models.CharField ("Class Section", max_length=1, choices=CLASS_SECTIONS)
    grade = models.ForeignKey ("Level")

    def save (self, *args, **kwargs):
        if self.id == None: # object is bein created for the first time
            super (ClassRoom, self).save(*args, **kwargs) # saving object

            LEVEL = self.grade.grade
            SECTION = self.section
            for S in self.grade.subject.all():
                if not Permission.objects.filter (codename = (u""+ LEVEL +"_"+ SECTION +"_"+ S.__unicode__())).exists(): # creating...
                    # Permission Structure
                    # codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
                    # name:     {Level.grade}-{ClassRoom.section}: {Subject.name}
                    NEW_P = Permission ()
                    NEW_P.name = u""+ LEVEL +"-"+ SECTION +": "+ S.__unicode__()
                    NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
                    NEW_P.codename = u""+ LEVEL +"_"+ SECTION +"_"+ S.__unicode__()
                    NEW_P.save()

            NEW_P = Permission ()
            NEW_P.name = u"Head Teacher of "+ self.grade.grade +"-"+ self.section
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
            NEW_P.codename = u"H_"+ self.grade.grade +"_"+ self.section
            NEW_P.save()

        else: # object is being edited...
            PREVIOUS_CLASSROOM = ClassRoom.objects.get (pk = self.id) # we know this exists!
            PREVIOUS_GRADE = PREVIOUS_CLASSROOM.grade

            super (ClassRoom, self).save(*args, **kwargs)

            if self.__unicode__() != PREVIOUS_CLASSROOM.__unicode__(): # There has been change in the object, Permissions update is necessary
                """
                NOTE:
                    - On permission, when a class is changed say from 1A to 1B or 2A: we will assume (for permission sake) 1B is a different class!
                    - i.e. all permissions associated with 1A will be removed, and new Permissions for 1B will be created
                """

                Permission.objects.filter (codename__istartswith = PREVIOUS_GRADE.grade +"_"+ PREVIOUS_CLASSROOM.section +"_").delete() # Deleting all associated permissions with the previous class room object
                Permission.objects.filter (codename = u"H_" + PREVIOUS_GRADE.grade +"_"+ PREVIOUS_CLASSROOM.section).delete()

                for S in self.grade.subject.all(): # Creating permissions for the NEW class room
                    NEW_P = Permission()
                    NEW_P.codename = self.grade.grade +"_"+ self.section +"_"+ S.name
                    NEW_P.name = self.grade.grade +"-"+ self.section +": "+ S.name
                    NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
                    NEW_P.save()

                NEW_P = Permission ()
                NEW_P.name = u"Head Teacher of "+ self.grade.grade +"-"+ self.section
                NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
                NEW_P.codename = u"H_"+ self.grade.grade +"_"+ self.section
                NEW_P.save()

        if not Permission.objects.filter (codename = "generate_report_card").exists():
            NEW_P = Permission ()
            NEW_P.codename = "generate_report_card"
            NEW_P.name = "Can Generate Report Card"
            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
            NEW_P.save()

    def __unicode__ (self):
        #return u""+ self.grade.__unicode__() +"-"+ str(self.section)
        return u"{}-{}".format (self.grade, self.section)

    def student_count (self):
        """ Returns the number of students attending in the class """

        return self.student_set.count()

    class Meta:
        verbose_name = "Class Room"
        verbose_name_plural = "Class Rooms"
        ordering = ["grade"]
        unique_together = (("section", "grade"),)

class Subject (models.Model):
    """ Holds Subjects given by the school """

    name = models.CharField ("Subject Name", max_length=125, unique=True)
    name_a = models.CharField ("የትምህርት ዓይነት", max_length=125, unique=True)
    given_in_semister_only = models.BooleanField ("Given Only On Semesters")
    use_letter_grading = models.BooleanField ("Convert to Letter Grading System") # We'll be using predefined scale--it won’t be like in collage or anything

    def __unicode__ (self):
        #return u""+ self.name
        return u"{}".format (self.name)

    def clean (self):
        self.name = self.name.title()
        self.name_a = self.name_a.title()

    def save (self, *args, **kwargs):
        """ This save override is used to update permission i.e. when a subject name is edited the permission name should be updated accordingly """

        if self.id == None: # Object being created for the first time, no permission change necessary
            super (Subject, self).save(*args, **kwargs)

        else: # object is being edited, permission update is necessary IF subject is given in a class room
            PREVIOUS_SUBJECT_NAME = Subject.objects.get (pk = self.id).name

            for L in Subject.objects.get (pk = self.id).level_set.all():
                for C in L.classroom_set.all():
                    if Permission.objects.filter (codename = u""+ L.grade +"_"+ C.section +"_"+ PREVIOUS_SUBJECT_NAME).exists(): # Updating Permission is necessary
                        Permission.objects.filter (codename = u""+ L.grade +"_"+ C.section +"_"+ PREVIOUS_SUBJECT_NAME).update (codename = u""+ L.grade +"_"+ C.section +"_"+ self.name, name = u""+ L.grade +"-"+ C.section +": "+ self.name)

            super (Subject, self).save(*args, **kwargs)

    """
    def delete (self, *args, **kwargs):
        "" Cleaning up before deleting, IF a subject is associated with permission, delete the permission ""

        for L in self.level_set.all():
            for C in L.classroom_set.all():
                Permission.objects.filter (codename = u""+ L.grade +"_"+ C.section +"_"+ self.name).delete()

        # Done cleaning, passing control to super delete
        super (Subject, self).delete(*args, **kwargs)
    """

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["name"]
        unique_together = (("name", "name_a"),)

class Level (models.Model):
    """ Holds list of Subjects given in a particular grade level """

    grade_choices = (("1", "Grade 1"), ("2", "Grade 2"), ("3", "Grade 3"), ("4", "Grade 4"), ("5", "Grade 5"), ("6", "Grade 6"), ("7", "Grade 7"), ("8", "Grade 8"), ("9", "Grade 9"), ("10", "Grade 10"), ("11S", "Grade 11 (Science)"), ("11A", "Grade 11 (Art)"), ("12S", "Grade 12 (Science)"), ("12A", "Grade 12 (Art)"))
    grade = models.CharField ("Grade Level", max_length=5, choices=grade_choices, unique=True)
    subject = models.ManyToManyField (Subject)

    def subject_count (self):
        """ Returns number of subjects given in level self """

        return str (self.subject.count())

    def save (self, *args, **kwargs):
        PREVIOUS_LEVEL = None

        if self.id != None: # Testing whether or not the object is being edited or being created
            PREVIOUS_LEVEL = Level.objects.get (pk = self.id)

        super (Level, self).save(*args, **kwargs)

        if PREVIOUS_LEVEL != None: # If we know the object is being edited, we have to test whether or not the object is affiliated with permissions if true permission updates necessary
            if self.grade != PREVIOUS_LEVEL.grade: # if change in grade occurred, we have to remove all permissions associated with the previous grade level
                Permission.objects.filter (codename__istartswith = PREVIOUS_LEVEL.grade +"_").delete() # Deleted all associated permissions with the previous grade

                if self.classroom_set.count(): # Testing whether or not the edited level object is associated with class room, if so NEW permission set is necessary
                    for CR in self.classroom_set.all():
                        for S in self.subject.all():
                            # Permission Structure
                            # codename: {Level.grade}_{ClassRoom.section}_{Subject.name}
                            # name:     {Level.grade}-{ClassRoom.section}: {Subject.name}
                            NEW_P = Permission()
                            NEW_P.codename = self.grade +"_"+ CR.section +"_"+ S.name
                            NEW_P.name = self.grade +"-"+ CR.section +": "+ S.name
                            NEW_P.content_type = ContentType.objects.get (app_label="condor", model="classroom")
                            NEW_P.save()

    def __unicode__ (self):
        #return u""+ self.grade
        return u"{}".format (self.grade)

    class Meta:
        verbose_name = "Level"
        verbose_name_plural = "Levels"

class GradeReport (models.Model):
    """ Holds Students Grade Report. NOTE: this object should not be used directly! """

    student = models.ForeignKey (Student)
    subject = models.ForeignKey (Subject)
    academic_calendar = models.ForeignKey (AcademicCalendar, limit_choices_to = {"semester_status": True})
    mark = models.DecimalField ("Score", max_digits=5, decimal_places=2, validators=[validate_mark])

    def __unicode__ (self):
        #return u""+ self.student.__unicode__() + " [" + self.subject.__unicode__() + ": "+ str(self.mark) +"]"
        return u"{} [{}: {}]".format (self.student, self.subject, self.mark)

    class Meta:
        verbose_name = "Grade Report"
        verbose_name_plural = "Grade Reports"
        unique_together = (("student", "subject", "academic_calendar"),)
        ordering = ["student"]

class Attendance (models.Model):
    """ Holds attendance sheet """

    academic_semester = models.ForeignKey (AcademicCalendar, limit_choices_to= {"semester_status": True})
    attendance_type_option = (("FULL", "Whole Day"), ("LATE", "Late"))
    attendance_type = models.CharField (max_length=5, choices=attendance_type_option)
    student = models.ManyToManyField (Student, blank = True)
    attendance_date = models.DateField ("Date")

    def __unicode__ (self):
        #return str (self.attendance_date) +": "+ self.attendance_type.title()
        return u"{}: {}".format (self.attendance_date, self.attendance_type)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        unique_together = (("attendance_date", "attendance_type", "academic_semester"),)
        ordering = ["-attendance_date"]

# Assigning signal listeners
# The signal listener will be called ERY time an object is being deleted either individually or via queryset
# NOTE: Overriding the delete or delete_model will NOT apply when an object is being deleted via queryset, So it's safe to use signals instead
pre_delete.connect (pre_delete_cleaner, sender = Level)
pre_delete.connect (pre_delete_cleaner, sender = Subject)
pre_delete.connect (pre_delete_cleaner, sender = ClassRoom)
