from django.test import TestCase
from emr.models import *
from django.contrib.auth import authenticate


class RegistrationTests(TestCase):

    def test_register_a_patient_by_form(self):
        """Attempt To register a user and make sure they show up in the database"""

    def test_register_a_patient_twice(self):
        """Attempt to register a patient twice, make sure the appropriate message is displayed"""
        # TODO: determine what message is returned

    def test_invalid_insurace_numer(self):
        """Attept to register a user with an invalid insurance Number, make sure it redirects to health insurance website"""


class LoginTests(TestCase):

    def test_login_form_patient(self):
        """Create a new patient and attempt to login as that user"""

        UN = "testpatient"
        PW = "passpass"

        # User object
        userpatient = User.objects.create_user(
            username=UN,
            password=PW,
            email="test@test.com",
            first_name="Pablo",
            last_name="Escobar")
        userpatient.save()

        # EMR object
        emr = EMR.objects.create()
        emr.save()

        # Hospital Object
        h = Hospital.objects.create(name="Sacred Heart")
        h.save()

        # Doctor Object
        ud = User.objects.create_user(
            username="drOctopus",  # cleaned_data is autogenerated data. can be modified in form
            password="pass",
            email="octo@puss.com",
            first_name="Doctor",
            last_name="Octopus"
        )
        ud.save()
        d = Doctor.objects.create(user=ud)
        d.hospitals.add(h)
        d.save()

        # patient object
        p = Patient.objects.create(
            user=userpatient,
            doctor=d,
            hospital=h,
            emr=emr)
        p.save()


        #todo add form data instead of directly creating the user

        # how to do:
            # create a form data and have it filled with all of the fields in the form


        testuser = authenticate(username = UN, password = PW)
        self.assertIsNotNone(testuser) # tests if anything is created


    def test_login_form_nurse(self):
        """Create a new nurse and attempt to login"""

    def test_login_form_doctor(self):
        """Create a new Doctor and attempt to login as doctor"""

    def attempt_to_login_with_fake_user(self):
        """Attempt to login with fake user and make sure it redirects to approprate page"""
        # TODO: figure out what page it would redrect to

