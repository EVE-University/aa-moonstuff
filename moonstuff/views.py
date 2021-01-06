from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as gt

from allianceauth.authentication.decorators import permissions_required
from .tasks import process_scan


# Create your views here.
@login_required
@permission_required('moonstuff.access_moonstuff')
def dashboard(request):
    return render(request, 'moonstuff/base.html')
