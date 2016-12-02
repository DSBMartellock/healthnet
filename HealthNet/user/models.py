from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

# this extension of user represents a nurse

class Nurse(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    hospital = models.ForeignKey('hospital.Hospital', null=True, blank=True)
    accepted = models.BooleanField(default=False)


    def __str__(self):
        return self.user.get_full_name()

    def getType(self):
        return "nurse"

# this extension of user represents an admin

class HospitalAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null = True, blank = True)
    hospital = models.ForeignKey('hospital.Hospital', null=True, blank=True)
    user.is_staff = True

    def __str__(self):
        return self.user.get_full_name()

    def getType(self):
        return "hosAdmin"


# this extension of user represents a patient

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    hospital = models.ForeignKey('hospital.Hospital', null=True, blank=True)
    doctor = models.ForeignKey('Doctor', null=True, blank=True)
    insuranceNum = models.CharField(max_length=12, default="")
    address = models.CharField(max_length=50, default="")
    phone = models.CharField(max_length=10, default="")

    contact = models.ForeignKey('Contact', null=True, blank=True)

    accepted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name()

    def admittedHospital(self):
        if hasattr(self, 'emrprofile'):
            if hasattr(self.emrprofile, 'admit_status'):
                if hasattr(self.emrprofile.admit_status, 'hospital'):
                    return self.emrprofile.admit_status.hospital


    def profileFinished(self):
        auth=True
        auth &= not((self.hospital is None) or (self.doctor is None))
        auth &= (self.user.get_full_name() != '') and (self.phone != '') and (self.address != '')
        auth &= not(self.contact is None)

        return auth


    def getType(self):
        return "patient"


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=50)
    emphone = models.CharField(max_length=10)

    def updateFromUser(self):
        if not(self.user is None):
            self.full_name = self.user.get_full_name()

            if hasattr(self.user, 'patient'):
                self.emphone=self.user.patient.phone

#this extension of user represents a doctor

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    hospitals = models.ManyToManyField('hospital.Hospital')
    patientCap = models.IntegerField(default=5)  # maximum number of patients a doctor can have
    nurses = models.ManyToManyField('Nurse')
    accepted = models.BooleanField(default=False)

    def acceptedPatients(self):
        return self.patient_set.all().filter(accepted=True)

    def __str__(self):
        return self.user.get_full_name()

    def getType(self):
        return "doctor"


class Event(models.Model):
    APP_BUFFER = datetime.timedelta(minutes=15)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True)
    hospital = models.ForeignKey('hospital.Hospital', null=True, blank=True)
    startTime = models.DateTimeField(default=timezone.now)
    endTime = models.DateTimeField()
    description = models.CharField(max_length=200, default="")
    appointment = models.BooleanField(default=False)

    visible = models.BooleanField(default=True)


    def conflicts(self):
        """This method checks for conflicting events. This method should be run before saving any event
        0 - No conflicts
        1 - The event is too long and extends into another event
        2 - The event starts before the end of another event
        """

        d_event_set = self.doctor.event_set.all().exclude(visible=False).exclude(pk=self.pk)

        if d_event_set.filter(startTime__lte=self.endTime).filter(startTime__gte=self.startTime).count() != 0:
            return 1
        if d_event_set.filter(endTime__lte=self.endTime).filter(endTime__gte=self.startTime).count() != 0:
            return 2

        if self.appointment:
            p_event_set = self.patient.event_set.all().exclude(visible=False).exclude(pk=self.pk)
            if p_event_set.filter(startTime__lte=self.endTime+Event.APP_BUFFER).filter(startTime__gte=self.startTime-Event.APP_BUFFER).count() != 0:
                return 1
            if p_event_set.filter(endTime__lte=self.endTime).filter(endTime__gte=self.startTime).count() != 0:
                return 2

        return 0

    def getType(self):
        return "event"


class Notification(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    title = models.CharField(max_length=50, default="")
    content = models.CharField(max_length=200, default="")
    link = models.CharField(max_length=10, default="")

    @staticmethod
    def push(user, title, content, link):
        return Notification.objects.create(user=user, title=title, content=content, link=link)





