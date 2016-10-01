from django.db import models

from Calendar.models import Calendar, Notification
from hospital.models import Hospital
from emr.models import EMR


# Create your models here.
class User(models.Model):

    Calendar = models.OneToOneField(Calendar, null=True, blank=True)
    UserName = models.CharField(max_length=15, default="")
    Password = models.CharField(max_length=20, default="")
    Notification = models.ManyToManyField(Notification, null=True, blank=True)

    firstName = models.CharField(max_length=20, default="")
    lastName = models.CharField(max_length=20, default="")

    def __str__(self):
        return self.firstName + ", " + self.lastName


    class Meta:
        abstract = True


# this extension of User represents a patient
class Patient(User):
    hospital = models.ForeignKey(Hospital, null=True, blank=True)
    doctor = models.ForeignKey('Doctor', null=True, blank=True)
    insuranceNum = models.CharField(max_length=12, default="")
    emr = models.OneToOneField(EMR, null=True, blank=True)


class Doctor(User):
    hospitals = models.ManyToManyField(Hospital)
    patientCap = models.IntegerField(default=0)  # maximum number of patients a doctor can have

    # TODO: add methods as they are needed,

