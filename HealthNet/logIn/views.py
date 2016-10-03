from django.shortcuts import render, get_object_or_404

from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response


#todo see if needed

# from User.models import *
# from .forms import PatientForm

# Create your views here.

@csrf_protect #add security
def register(request):
    form = RegistrationForm(request.POST)
    if form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],  # cleaned_data is autogenerated data. can be modified in form
            password=form.cleaned_data['password1'],
            email=form.cleaned_data['email']
        )
        return HttpResponseRedirect('accounts/profile/')
    else:
        form = RegistrationForm()
        variables = RequestContext(request, {'form': form})
        return render_to_response('registration/register.html', variables)

def register_success(request):
    return render_to_response('registration/success.html')

def logout_page(request):
    logout(request)

@login_required
def home(request):
    return render_to_response('home.html',{'user': request.user })


# def index(request):
#
#     return render(request, 'logIn/index.html')


# def authenticate(request):
#     response = 'neutral'
#     #queryset
#     patientquery = Patient.objects.filter(UserName=request.POST['UN'])
#
#     if patientquery.exists():
#         response = 'well the username exists'
#         passfromdb = patientquery.values('Password')[0]['Password']
#         if passfromdb == request.POST['PW']:
#             response = response +' hell yeah you in'
#         else:
#             response = response+ ' gettt outta here with that password tho'
#     else:
#         response = 'username does not exist'
#     return HttpResponse(response )


#todo see if you can add other params to a generic user paramater
# class Register(CreateView):
#     model = Patient
#     template_name = 'login/register_form.html'
#     form_class = PatientForm

