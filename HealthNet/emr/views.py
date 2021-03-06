from PIL import Image
from django.core.urlresolvers import reverse
from django.http import HttpResponse , HttpResponseRedirect
from django.shortcuts import render , get_object_or_404
from django.views.generic import DetailView, View
import HealthNet.viewhelper as viewhelper


from HealthNet import userauth
from HealthNet import notificaion
from syslogging.models import *
from user.models import *
from django.core.urlresolvers import reverse
from .forms import *
import json


def getFilterForm(user):
    if hasattr(user.user, 'filterform'):
        return user.user.filterform
    return FilterForm.objects.create(user=user.user)


def viewSelfEmr(request):
    cuser = viewhelper.get_user(request)
    if cuser is None:
        return HttpResponseRedirect(reverse('login'))
    return HttpResponseRedirect(reverse('emr:vemr', args={cuser.pk}))


def feedBackView(request, *args):
    return HttpResponse("content")


def editEmrProfile(request, pk):
    user = viewhelper.get_user(request)
    if user is None:
        viewhelper.unauth(request)

    patient = get_object_or_404(Patient, pk=pk)

    if not userauth.userCan_EMR(user, patient, 'vitals'):
        return viewhelper.unauth(request)

    form = None

    if request.method == "GET":
        form = ProfileCreateForm()
        if hasattr(patient, 'emrprofile'):
            form.defaults(patient.emrprofile)
    elif request.method == "POST":
        form = ProfileCreateForm(request.POST)

        if form.is_valid():
            m = None
            if hasattr(patient, 'emrprofile'):
                m = form.save(commit=False, model=patient.emrprofile)
            else:
                m = form.save(commit=False)

            m.patient = patient
            # TODO: notification
            m.save()
            return HttpResponseRedirect(reverse('emr:vemr', args=(pk,)))

    return render(request, 'emr/emritem_edit.html'
                  , viewhelper.getBaseContext(request, user, form=form,
                                                            title="Edit {0}'s Basic Health Information".format(patient.user.get_full_name()),
                                                            patient=patient))


###################EMR AJAX########################


def emrActionAjax(request, pk):
    pkdict = json.loads(request.body.decode("utf-8"))
    if 'emrpk' in pkdict and 'action' in pkdict:
        item = get_object_or_404(EMRItem, pk=pkdict['emrpk'])

        if isTest(item):
            if pkdict['action'] == 'releasehide':
                bool = item.emrtest.released
                item.emrtest.released = not bool
                item.emrtest.save()
        elif isPrescription(item):
            if pkdict['action'] == 'stop':
                item.endDate = timezone.now()
        else:
            return HttpResponse("PASS")

        item.save()
    return HttpResponse("PASS")


###################EMR AJAX##########################

def getFormFromReqType(mtype, patient, provider, post=None, files=None):
    form = None
    if mtype == 'test':
        if post != None:
            form = TestCreateForm(post, files)
        else:
            form = TestCreateForm(initial={'patient': patient.pk})
    elif mtype == 'vitals':
        if post != None:
            form = VitalsCreateForm(post, initial={'patient': patient.pk})
        else:
            form = VitalsCreateForm(initial={'patient': patient.pk})
    elif mtype == 'note':
        if post != None:
            form = EMRItemCreateForm(post, initial={'patient': patient.pk})
        else:
            form = EMRItemCreateForm(initial={'patient': patient.pk})
    elif mtype == 'prescription':
        if post != None:
            form = prescriptionCreateForm(post, initial={'patient': patient.pk, 'proivder': provider.user.pk})
        else:
            form = prescriptionCreateForm(initial={'patient': patient.pk, 'proivder': provider.user.pk})
    elif mtype == "admitdischarge":
        if post != None:
            form = AdmitDishchargeForm(post)
        else:
            form = AdmitDishchargeForm()

    return form


#####################################VIEW EMR#####################################
def getPermissionsContext(cuser, patient):
    return {'canEdit': userauth.userCan_EMR(cuser, patient, 'edit'),
            'canVitals': userauth.userCan_EMR(cuser, patient, 'vitals'),
            'canAdmit': userauth.userCan_EMR(cuser, patient, 'admit'),
            'canPrescribe': userauth.userCan_EMR(cuser, patient, 'prescribe')}


def viewEMR(request, pk):
    user = viewhelper.get_user(request)
    if user is None:
        return viewhelper.unauth(request)

    patient = get_object_or_404(Patient, pk=pk)

    if not userauth.userCan_EMR(user, patient, 'view'):
        # TODO: add syslogging to unauth, Syslog.unauth_acess(request)
        return viewhelper.unauth(request)

    emr = patient.emritem_set.all().order_by('-date_created')

    form=None
    ff = getFilterForm(user)
    if request.method == "POST":
        form = FilterSortForm(request.POST, instance=ff)
        if form.is_valid():
            form.save(commit=True)
    else:
        form = FilterSortForm(instance=ff)

    if not(ff is None):
        if ff.filters != "":
            build = emr.none()
            if 'prescription' in ff.filters:
                build |= emr.exclude(emrprescription=None)
            if 'vitals' in ff.filters:
                build |= emr.exclude(emrvitals=None)
            if 'test' in ff.filters:
                build |= emr.exclude(emrtest=None)
            if 'pending' in ff.filters:
                build |= emr.filter(emrtest__released=False)
            if 'admit' in ff.filters:
                build |= emr.filter(emradmitstatus__admit=True)
            if 'discharge' in ff.filters:
                build |= emr.filter(emradmitstatus__admit=False)
            emr = build

        if ff.keywords != "":
            build = emr.none()
            words = ff.keywords.split(' ')
            for word in words:
                build |= emr.filter(content__contains=word)
                build |= emr.filter(emrvitals__bloodPressure__contains=word)

                if viewhelper.try_parse(word):
                    num = int(word)
                    build |= emr.filter(priority=num)
                    build |= emr.filter(emrprescription__dosage=num)
                    build |= emr.filter(emrprescription__amountPerDay=num)
                    build |= emr.filter(emrvitals__height=num)
                    build |= emr.filter(emrvitals__weight=num)

            emr = build

        if ff.sort != "":
            if 'date' in ff.sort:
                emr = emr.order_by('-date_created')
            elif 'priority' in ff.sort:
                emr = emr.order_by('-priority')
            elif 'alph' in ff.sort:
                emr = emr.order_by('content')
            elif 'vitals' in ff.sort:
                emr = list(emr.exclude(emrvitals=None)) + list(emr.filter(emrvitals=None))

    ctx = {'EMRItems': emr, 'form': form, 'patient': patient,
           'permissions': getPermissionsContext(user, patient),
           'admit': viewhelper.isAdmitted(patient)}

    if ctx['admit']:
        ctx['hospital'] = patient.admittedHospital()

    if hasattr(patient, 'emrprofile'):
        ctx['EMRProfile'] = patient.emrprofile

    Syslog.viewEMR(patient, user)

    return render(request, 'emr/filter_emr.html', viewhelper.getBaseContext(request, user, title="{0}'s Electronic Medical Record".format(patient.user.get_full_name()), **ctx))


def viewEmrItem(request, pk):
    user = viewhelper.get_user(request)
    if user is None:
        return viewhelper.unauth(request)

    item = get_object_or_404(EMRItem, pk=pk)

    if not userauth.userCan_EMR(user, item.patient, 'view'):
        # TODO: add syslogging to unauth, Syslog.unauth_acess(request)
        return viewhelper.unauth(request)
    return render(request, 'emr/view_emr_item.html', viewhelper.getBaseContext(request, user, item=item, title="Medical Record Detail", permissions=getPermissionsContext(user, item.patient)))


def exportEMR(request, pk):
    user = viewhelper.get_user(request)
    if user is None:
        return viewhelper.unauth(request)

    patient = get_object_or_404(Patient, pk=pk)

    if not userauth.userCan_EMR(user, patient, 'view'):
        # TODO: add syslogging to unauth, Syslog.unauth_acess(request)
        return viewhelper.unauth(request)

    emr = patient.emritem_set.all().order_by('-date_created')

    ctx = {'patient': patient, 'user': user, 'EMRItems': emr}
    if hasattr(patient, 'emrprofile'):
        ctx['EMRProfile'] = patient.emrprofile

    return render(request, 'emr/export_emr.html', ctx)


def canCreateEditEmr(mtype, patient, provider):
    auth = True
    auth |= mtype in ['item', 'test', 'vitals', 'profile'] and userauth.userCan_EMR(provider, patient, 'edit')
    auth |= mtype == 'prescription' and userauth.userCan_EMR(provider, patient, 'prescribe')
    auth |= mtype in ['vitals', 'profile'] and userauth.userCan_EMR(provider, patient, 'vitals')
    return auth


def EMRItemCreate(request, pk, type):

    cuser = viewhelper.get_user(request)
    if cuser is None:
        return HttpResponseRedirect(reverse('login'))

    patient = get_object_or_404(Patient, pk=pk)

    if not canCreateEditEmr(type, patient, cuser):
        return viewhelper.toEmr(request, patient.pk)


    if request.method == "POST":
        form = getFormFromReqType(type, patient, cuser, post=request.POST, files=request.FILES)

        if form.is_valid():
            m = form.save(commit=False, patient=patient)


            if isPrescription(m):

                m.provider = cuser

            m.save()


            return HttpResponseRedirect(reverse('emr:vemr', args=(patient.pk,)))

    else:
        form = getFormFromReqType(type, patient, cuser)

    return render(request, 'emr/emritem_edit.html', viewhelper.getBaseContext(request, cuser, title="Add {0} to {1}'s Electronic Medical Record".format(type, patient.user.get_full_name()), form=form, patient=patient))


def editAdmitDischarge(request, emritem):
    user = viewhelper.get_user(request)
    if user is None:
        viewhelper.unauth(request)

    if not userauth.userCan_EMRItem(user, emritem, 'edit'):
        viewhelper.unauth(request)

    #TODO: allow hospital admin to edit all admission fields

    form = None
    if request.method == "POST":
        form = AdmitDishchargeForm(request.POST)
        if form.is_valid():
            m = form.save(commit=True, update=emritem)
            return viewhelper.toEmr(request, emritem.patient.pk)
    else:
        form = AdmitDishchargeForm()
        form.defaults(emritem)

    form.lockField('hospital', emritem.emradmitstatus.hospital)
    form.lockField('patient', emritem.patient)

    return render(request, 'emr/emritem_edit.html', viewhelper.getBaseContext(request, user, form=form, patient=emritem.patient))


def editEmrItem(request, pk):
    user = viewhelper.get_user(request)
    if user is None:
        return viewhelper.unauth(request)

    emritem = get_object_or_404(EMRItem, pk=pk)

    if not userauth.userCan_EMRItem(user, emritem, 'edit'):
        return viewhelper.unauth(request)

    if hasattr(emritem, 'emradmitstatus'):
        return editAdmitDischarge(request, emritem)

    form = None

    if request.method == "GET":
        form = getFormFromReqType(emrItemType(emritem), emritem.patient, user)
        form.defaults(emritem)
    else:
        form = getFormFromReqType(emrItemType(emritem), emritem.patient, user, post=request.POST,
                                       files=request.FILES)
        if form.is_valid():
            if isPrescription(emritem):
                m = form.save(update=emritem, commit=False)
                m.emrprescription.provider = user
                m.emrprescription.save()
                m.save()
            else:
                form.save(update=emritem, commit=True)

            return HttpResponseRedirect(reverse('emr:vemri', args=(emritem.pk,)))

    return render(request, 'emr/emritem_edit.html', viewhelper.getBaseContext(request, user, form=form, patient=emritem.patient))


class AdmitDishchargeView(DetailView):
    model = Patient
    type=None

    def kick(self, patient):
        return HttpResponseRedirect(reverse('emr:vemr', args=(patient.pk,)))

    def get(self, request, **kwargs):
        cuser = viewhelper.get_user(request)
        if cuser is None:
            return HttpResponseRedirect(reverse('login'))

        patient = self.get_object()

        if not canCreateEditEmr(self.type, patient, cuser) or not userauth.userCan_EMR(cuser, patient, 'admit'):
            return self.kick(patient)

        form = AdmitDishchargeForm()

        title=""

        if patient.admittedHospital() is None:
            if not userauth.userCan_EMR(cuser, patient, 'admit'):
                return self.kick(patient)

            title = "Admission Form"
            form.lockField('admit', True)

            if cuser.getType() in ['nurse', 'hosAdmin']:
                form.lockField('hospital', cuser.hospital)
                form.fields['hospital'].queryset = Hospital.objects.all().filter(pk=cuser.hospital.pk)
            elif cuser.getType() == 'doctor':
                form.fields['hospital'].queryset = cuser.hospitals.all()


        else:
            if not userauth.userCan_EMR(cuser, patient, 'discharge'):
                return self.kick(patient)

            title = "Discharge Form"
            form.lockField('admit', False)

            form.lockField('hospital', '')


        return render(request, 'emr/emritem_edit.html', viewhelper.getBaseContext(request, cuser, form=form, patient=patient, title=title))


    def post(self, request, **kwargs):
        cuser = viewhelper.get_user(request)
        if cuser is None:
            return HttpResponseRedirect(reverse('login'))

        patient = self.get_object()

        form = AdmitDishchargeForm(request.POST)
        ctx = {'user': cuser, 'form': form}

        title=None

        mdict = {}

        if patient.admittedHospital() is None:
            ctx['formtitle'] = "Admission Form"
            mdict['title'] = "Admission"


            if cuser.getType() in ['nurse', 'hosAdmin']:
                form.lockField('hospital', cuser.hospital.pk)
                mdict['hospital'] = cuser.hospital
            elif cuser.getType() == 'doctor':
                form.fields['hospital'].queryset = cuser.hospitals.all()

        else:
            ctx['formtitle'] = "Discharge Form"
            form.lockField('admit', False)
            form.lockField('hospital', '')
            mdict['title']="Discharge"
            mdict['admit']=False


        if form.is_valid():
            m = form.save(commit=False, patient=patient, provider=cuser)

            viewhelper.add_dict_to_model(mdict, m)
            m.save()

            if not hasattr(patient, 'emrprofile'):
                patient.emrprofile = EMRProfile.objects.create()
                patient.save()

            patient.emrprofile.admit_status = m
            patient.emrprofile.save()
            patient.save()

            return HttpResponseRedirect(reverse('emr:vemr', args=(patient.pk,)))
        else:
            return render(request, 'emr/emritem_edit.html', viewhelper.getBaseContext(request, cuser, form=form, patient=patient))


def serveTestMedia(request, pk):
    cuser = viewhelper.get_user(request)
    if cuser is None:
        return HttpResponseRedirect(reverse('login'))

    emritem = get_object_or_404(EMRItem, pk=pk)
    patient = emritem.patient

    path = None

    if hasattr(emritem, 'emrtest'):
        if emritem.emrtest.released or userauth.userCan_EMR(cuser, patient, 'view_full'):
            try:
                with open(emritem.emrtest.images.path, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/jpeg")
            except IOError:
                return getBlankImage()
    return getBlankImage()


def getBlankImage():
    red = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
    response = HttpResponse(content_type="image/jpeg")
    red.save(response, "JPEG")
    return response











