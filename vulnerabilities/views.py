# Copyright (c) 2017 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/vulnerablecode/
# The VulnerableCode software is licensed under the Apache License version 2.0.
# Data generated with VulnerableCode require an acknowledgment.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with VulnerableCode or any VulnerableCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with VulnerableCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  VulnerableCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  VulnerableCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/vulnerablecode/ for support and download.

from itertools import chain

from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views import View

from vulnerabilities.forms import PackageForm, VulnerabilitySearchForm
from vulnerabilities.models import Package, ImpactedPackage, ResolvedPackage, VulnerabilityReference, Vulnerability

class PackageSearchView(View):
    template_name = "packages.html"

    def get(self, request):
        context = {'form': PackageForm()}

        if request.GET :
            packages = _to_queryset(request)
            context['packages'] = packages

        return render(request, self.template_name, context)

def _to_queryset(request):
    query = {}
    if len(request.GET['name']) :
        query['name'] = request.GET['name']

    if request.GET['type'] and request.GET['type'] != '*' :
        query['type'] = request.GET['type']

    if len(request.GET['version']) :
        query['version'] = request.GET['version']

    return Package.objects.all().filter(**query)

class VulnerabilitySearchView(View):

    template_name = "vulnerabilities.html"

    def get(self, request):
        context = {'form' : VulnerabilitySearchForm() }

        if request.GET :
            vulnerabilities = self._to_queryset(request)
            context['vulnerabilities'] = vulnerabilities

        return render(request, self.template_name, context)

    def _to_queryset(self,request):

        if request.GET['vuln_id'] :
            vuln_id = request.GET['vuln_id']
            return Vulnerability.objects.filter(cve_id__contains=vuln_id).select_related()

class PackageUpdate(UpdateView):

    template_name = "package_update.html"
    model = Package
    fields = ['name', 'type', 'version', 'namespace']

    def get_context_data(self, **kwargs):
        context = super(PackageUpdate, self).get_context_data(**kwargs)
        resolved_vuln, unresolved_vuln = self._package_vulnerabilities(self.kwargs['pk'])
        context['resolved_vuln'] = resolved_vuln
        context['impacted_vuln'] = unresolved_vuln

        return context

    def _package_vulnerabilities(self, package_pk) :

        ip = ImpactedPackage.objects.filter(package_id=package_pk).select_related()
        rp = ResolvedPackage.objects.filter(package_id=package_pk).select_related()

        resolved_vuln = [i.vulnerability for i in  rp]
        unresolved_vuln = [i.vulnerability for i in  ip]

        return resolved_vuln, unresolved_vuln


    def get_success_url(self):
        return ''

class VulnerabilityDetails(ListView):
    template_name = 'vulnerability.html'
    model = VulnerabilityReference

    def get_context_data(self, **kwargs):
        context = super(VulnerabilityDetails, self).get_context_data(**kwargs)
        context['vulnerability'] =  Vulnerability.objects.get(id=self.kwargs['pk'])
        return context

    def get_queryset(self):
        return VulnerabilityReference.objects.filter(vulnerability_id=self.kwargs['pk'])

class VulnerabilityCreate(CreateView):

    template_name = "vulnerability_create.html"
    model = Vulnerability
    fields = ['cve_id', 'summary']

    def get_success_url(self):

        return reverse('vulnerability_view', kwargs={'pk':self.object.id})

class PackageCreate(CreateView):

    template_name = "package_create.html"
    model = Package
    fields = ['name','namespace','type','version']

    def get_success_url(self):
        return reverse('package_view', kwargs={'pk' : self.object.id})

class ResolvedPackageDelete(DeleteView):

    model = ResolvedPackage

    def get_object(self):
        package_id = self.kwargs.get('pid')
        vulnerability_id = self.kwargs.get('vid')
        return ResolvedPackage.objects.get(package_id=package_id, vulnerability_id=vulnerability_id)

    def get_success_url(self):
        return reverse('package_view', kwargs={'pk' : self.kwargs.get('pid')})

class ImpactedPackageDelete(DeleteView):

    model = ImpactedPackage

    def get_object(self):
        package_id = self.kwargs.get('pid')
        vulnerability_id = self.kwargs.get('vid')
        return ImpactedPackage.objects.get(package_id=package_id, vulnerability_id=vulnerability_id)

    def get_success_url(self):
        return reverse('package_view', kwargs={'pk' : self.kwargs.get('pid')})

class HomePage(View):

    template_name = "index.html"

    def get(self, request):
        return render(request, self.template_name)


class ImpactedPackageCreate(CreateView):

    template_name = 'impacted_package_create.html'
    model = ImpactedPackage 
    fields = ['vulnerability']

    def form_valid(self, form):

        package = Package.objects.get(id=self.kwargs['pid'])
        form.instance.package = package
        return super(ImpactedPackageCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('package_view', kwargs={'pk': self.kwargs['pid']})

class ResolvedPackageCreate(CreateView):

    template_name = 'resolved_package_create.html'
    model = ResolvedPackage 
    fields = ['vulnerability']

    def form_valid(self, form):

        package = Package.objects.get(id=self.kwargs['pid'])
        form.instance.package = package
        return super(ResolvedPackageCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('package_view', kwargs={'pk': self.kwargs['pid']})

class VulnerabilityReferenceCreate(CreateView):

    template_name = 'vulnerability_reference_create.html'
    model = VulnerabilityReference
    fields = ['reference_id','url']

    def form_valid(self, form):
        form.instance.vulnerability =  Vulnerability.objects.get(id=self.kwargs['vid'])
        return super(VulnerabilityReferenceCreate, self).form_valid(form)
    
    def get_success_url(self):
        return reverse('vulnerability_view', kwargs={'pk': self.kwargs['vid']})

