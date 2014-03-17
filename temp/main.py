#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib
import cgi
import json

import jinja2
import webapp2

import cloudstorage as gcs
import google.appengine.api.app_identity as app_id

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

BUCKET = '/distributeddrawing.appspot.com'
#BUCKET = '/' + str(app_id.get_default_gcs_bucket_name())


#This line taken from google app engine tutorial
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class DrawingPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('drawing.html')
        self.response.write(template.render(template_values))

class ThanksPage(webapp2.RequestHandler):
    def post(self):
        i = json.loads(self.request.body)
        print type(i)#print type(i) + ': '+i+' - HERE' #prints to log console
        #self.response.out.write('<html><body>%s</body></html>' % i) # prints to web page

        self.response.write("Thanks page loaded")

class Write(webapp2.RequestHandler):
    def post(self):
        filename = BUCKET + '/testfile'
        
        #read contents of file first
        gcs_file = gcs.open(filename)
        lines = (line.rstrip('\n') for line in gcs.open(filename))
        gcs_file.close()
        
        #now right to file
        gcs_file = gcs.open(filename,
        'w',
        content_type='text/plain')
        for line in lines:
            gcs_file.write(line)
        gcs_file.write(self.request.body)
        gcs_file.close()
        self.response.write("success")
        
class Read(webapp2.RequestHandler):
    def get(self):
        filename = BUCKET + '/testfile'
        gcs_file = gcs.open(filename)
        lines = (line.rstrip('\n') for line in gcs.open(filename))
        str = ''
        for line in lines:
            str += line
        self.response.write(str)
        gcs_file.close()
        
class Create(webapp2.RequestHandler):
    def get(self):
        filename = BUCKET + '/testfile'
        
        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        gcs_file = gcs.open(filename,
            'w',
            content_type='text/plain',
            options={'x-goog-meta-foo': 'foo',
                     'x-goog-meta-bar': 'bar'},
            retry_params=write_retry_params)
        gcs_file.write("This is the file:\n")
        gcs_file.close()

class Delete(webapp2.RequestHandler):
    def get(self):
        filename = BUCKET + '/testfile'
        gcs.delete(filename)
        
app = webapp2.WSGIApplication([
    ('/', DrawingPage),
    ('/thanks', ThanksPage),
    ('/read', Read),
    ('/write', Write),
    ('/create', Create),
    ('/del', Delete)
], debug=True)


'''
What i need to be recording is whatever I need to draw the line again programatically

'''

