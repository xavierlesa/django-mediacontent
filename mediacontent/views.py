# -*- coding:utf-8 -*-
import json

from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from mediacontent.models import MediaContent

class AjaxableResponseMixin(object):
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return self.render_to_json_response(data)
        else:
            return response

class AjaxMediaContentList(ListView):
    def get_queryset(self):
        pk = self.kwargs['pk']
        
        qs = MediaContent.objects.all()

        if self.kwargs.has_key('pk') and self.kwargs['pk']:
            qs = qs.filter(pk=pk)
        
        if self.kwargs.has_key('mimetype') and self.kwargs['mimetype']:
            qs = qs.filter(mimetype__startswith=self.kwargs['mimetype'])

        qs = qs.order_by('-pub_date')
        return qs
    
    def parse_queryset(self):
        qs = self.get_queryset()
        res = []

        for object in qs:
            temp = {}
            temp['id'] = object.pk
            temp['title'] = object.title
            temp['description'] = object.description
            if object.content:
                temp['url'] = object.content.url
            if object.gallery:
                temp['gallery_url'] = object.gallery.url
            if object.thumbnail:
                temp['thumbnail_url'] = object.thumbnail.url
            res.append(temp)
        
        if len(res) == 1:
            res = res[0]
        
        return json.dumps(res)

    def render_to_response(self, context, **kwargs):
        return HttpResponse(self.parse_queryset(), **kwargs)
        

class AjaxMediaContentCreate(AjaxableResponseMixin, CreateView):
    model = MediaContent

class AjaxMediaContentUpdate(AjaxableResponseMixin, UpdateView):
    model = MediaContent

class AjaxMediaContentDelete(DeleteView):
    model = MediaContent
    success_url = '/'

    def delete(self, request, *args, **kwargs):
        res = super(AjaxMediaContentDelete, self).delete(request, *args, **kwargs)
        if res:
            return HttpResponse(json.dumps('OK'), content_type='application/json')

class AjaxMediaAPIView(View):
    
    http_method_names = ['get', 'post', 'put', 'delete']

    def dispatch(self, *args, **kwargs):
        return super(AjaxMediaAPIView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        view = AjaxMediaContentList.as_view()
        return view(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        view = AjaxMediaContentUpdate.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = AjaxMediaContentCreate.as_view()
        return view(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        view = AjaxMediaContentDelete.as_view()
        return view(request, *args, **kwargs)
