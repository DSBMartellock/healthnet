from django.shortcuts import render
from user.models import *
from user.formvalid import dict_has_keys
from django.contrib import messages
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.contrib.auth.models import User
from hospital.models import *
from syslogging.models import *
from user.viewhelper import healthUserFromDjangoUser


#todo see if needed

# from User.models import *
# from .forms import PatientForm

# Create your views here.

class Register(View):

    def post(self, request):
        form = None

        if dict_has_keys(['username', 'password1', 'password2'], request.POST):
            form = RegistrationFormFull(request.POST)

            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    # cleaned_data is autogenerated data. can be modified in form
                    password=form.cleaned_data['password1'],
                )

                p = Patient.objects.create(user=user, insuranceNum=form.cleaned_data['insuranceNum'])
                p.save()

                user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
                login(request, user)

                Syslog.userCreate(p)
                return HttpResponseRedirect(reverse('user:eProfile'))

        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form = RegistrationFormFull(initial={'insuranceNum': form.cleaned_data['insuranceNum']})


        return render(request, 'registration/register.html', {'form': form})

    def get(self, request):
        form = RegistrationForm()
        variables = RequestContext(request, {'form': form})
        return render(request, 'registration/register.html', variables)

class UserSelect(View):
    def post(self, request):
        form = UserSelectForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data['typeOfUser'])
            if 'doctor' in form.cleaned_data['typeOfUser']:
                return HttpResponseRedirect(reverse('logIn:doctorRegister'))
            elif 'nurse' in form.cleaned_data['typeOfUser']:
                return HttpResponseRedirect(reverse('logIn:nurseRegister'))
        return render(request, 'registration/userSelect.html', {'form': form})

    def get(self, request):
        form = UserSelectForm()
        return render(request, 'registration/userSelect.html', {'form': form})

class DoctorRegister(View):
    def post(self, request):
        form = None

        if dict_has_keys(['username', 'password1', 'password2'], request.POST):
            form = DoctorRegistrationForm(request.POST)

            if form.is_valid():
                user = User.objects.create_user(
                    first_name=form.cleaned_data['firstName'],
                    last_name=form.cleaned_data['lastName'],
                    email=form.cleaned_data['email'],
                    username=form.cleaned_data['username'],
                    # cleaned_data is autogenerated data. can be modified in form
                    password=form.cleaned_data['password1'],
                )

                d = Doctor.objects.create(user=user)

                for hospital in form.cleaned_data['hospitals']:
                    d.hospitals.add(hospital)

                d.save()

                #user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
                #login(request, user)

                Syslog.userCreate(d)
                return HttpResponseRedirect(reverse('login'))

        else:
            form = DoctorRegistrationForm(request.POST)

        return render(request, 'registration/doctorRegister.html', {'form': form})

    def get(self, request):
        form = DoctorRegistrationForm()
        variables = RequestContext(request, {'form': form})
        return render(request, 'registration/doctorRegister.html', {'form': form}, variables)

class NurseRegister(View):
    def post(self, request):
        form = None

        if dict_has_keys(['username', 'password1', 'password2'], request.POST):
            form = NurseRegistrationForm(request.POST)

            if form.is_valid():
                user = User.objects.create_user(
                    first_name=form.cleaned_data['firstName'],
                    last_name=form.cleaned_data['lastName'],
                    email=form.cleaned_data['email'],
                    username=form.cleaned_data['username'],
                    # cleaned_data is autogenerated data. can be modified in form
                    password=form.cleaned_data['password1'],
                )

                n = Nurse.objects.create(user=user, hospital=form.cleaned_data['hospital'])
                n.save()

                Syslog.userCreate(n)
                return HttpResponseRedirect(reverse('login'))

        else:
            form = RegistrationForm(request.POST)

        return render(request, 'registration/nurseRegister.html', {'form': form})

    def get(self, request):
        form = NurseRegistrationForm()
        return render(request, 'registration/nurseRegister.html', {'form': form})

class LoginView(View):

    def post(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('user:dashboard'))

        lform = LoginForm(request.POST)

        if(lform.is_valid()):
            user = authenticate(username=lform.cleaned_data['username'], password=lform.cleaned_data['password'])

            print(user)
            if user is not None:
                if healthUserFromDjangoUser(user).getType() == 'doctor' or healthUserFromDjangoUser(user).getType() == 'nurse':
                    if healthUserFromDjangoUser(user).accepted == True:
                        login(request, user)
                        Syslog.userLogin(user)
                        return HttpResponseRedirect(reverse('user:dashboard'))
                    else:
                        return HttpResponseRedirect(reverse('login'))
                        #form = LoginForm()
                        #return render(request, 'logIn/index.html', {'something': True, 'form': form})
                login(request, user)
                Syslog.userLogin(user)
                return HttpResponseRedirect(reverse('user:dashboard'))

        return HttpResponseRedirect(reverse('login'))

    def get(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('user:dashboard'))

        form = LoginForm()

        return render(request, 'logIn/index.html', {'form': form})


def register_success(request):
    return render_to_response('registration/success.html')

def logout_page(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


@login_required
def home(request):
    return render_to_response('home.html',{'user': request.user })


