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


@login_required
@permission_required('moonstuff.add_resource')
def add_scan(request):
    if request.method == 'POST':
        scan_data = request.POST['scan']

        process_scan.delay(scan_data, request.user.id)
        messages.success(request, gt('Your moon scan is being processed. Depending on size this may take some time.'))
        return redirect('moonstuff:dashboard')

    return render(request, 'moonstuff/add_scan.html')
