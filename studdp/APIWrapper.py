import json
import logging
import os
import shutil
import signal
import time
import sys
import requests
import time

def retryUntilCondition(condition):
  def decorate(function):
    def f(*args, **kwargs):
      timeout = time.time() + 180
      while True:
        result = function(*args, **kwargs)
        if condition(result):
          return result
        elif time.time() > timeout:
          raise Exception("Unable to connect.")
          return
        elif "User may not access file" in result.text:
          raise Exception("Unable to access location.")
        time.sleep(0.5)
    return f
  return decorate

def responseIs200(response):
  return response.status_code == 200

class APIWrapper(object):
    """
    An API wrapper for the Stud.IP Rest.API.
    See studip.github.io/studip-rest.ip/ for details.
    """

    def __init__(self, auth, base_address, local_path):

        self._auth = auth
        self._base_address = base_address
        self.local_path = os.path.expanduser(local_path)

    def url(self, route):
        """
        Creates an URL from the configuration and the route.
        """
        return "%s%s" % (self._base_address, route)


    @retryUntilCondition(responseIs200)
    def get(self, route, stream=False):
        """
        Performs a GET request with the authentication from the configuration.
        Will raise errors that have to be handled by the user.
        """
        return requests.get(self.url(route), auth=self._auth, stream=stream)


    def get_courses(self):
        """
        Gets a list of courses.
        """
        return json.loads(self.get('/api/courses').text)["courses"]


    def get_course_folders(self, course):
        """
        Gets a list of document folders for a given course.
        """
        return json.loads(self.get('/api/documents/%s/folder' \
                                    % course['course_id']).text)['folders']


    def get_documents(self, course):
        """
        Gets a list of documents and folders inside a folder.
        """
        documents = []
        folders = self.get_course_folders(course)
        for i, folder in enumerate(folders):
            folders[i]['path'] = os.path.join(self.local_path, course['title'])

        while folders:
            folder = folders.pop()
            if folder["permissions"]["readable"] == False:
                continue
            try:
                path = '/api/documents/%s/folder/%s' \
                        % (course['course_id'], folder['folder_id'])
                temp = json.loads(self.get(path).text)
            except (ValueError, AttributeError):
                raise Exception('Error on loading %s.' % path)
                continue

            for key in ['folders', 'documents']:
                for i in range(len(temp[key])):
                    temp[key][i]['path'] = os.path.join(folder['path'],
                                                        folder['name'])
            documents += temp['documents']
            folders += temp['folders']
        return documents


    def download_document(self, document, path):
        """
        Downloads the document to docfile.
        Will raise exceptions that have to be handled.
        """
        try:
            file = self.get('/api/documents/%s/download' % document['document_id'], stream=True)
            os.makedirs(document['path'], exist_ok=True)
            with open(path, 'wb') as docfile:
                shutil.copyfileobj(file.raw, docfile)
        except Exception:
            raise
