import urllib2,urllib
import csv
import settings
import mimetools,itertools,mimetypes
import base64

def UnicodeDictReader(utf8_data, **kwargs):
  csv_reader = csv.DictReader(utf8_data, **kwargs)
  for row in csv_reader:
    yield dict([(key, unicode(value, 'utf-8')) for key, value
      in row.iteritems()])

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              'Content-Transfer-Encoding: BASE64',
              '',
              base64.b64encode(body),
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return u'\r\n'.join(flattened)


def post_record(r):
  print "uploading %s"%r["title"]
  fn=r.pop("file_data")
  form=MultiPartForm()
  for (k,v) in r.items():
    form.add_field(k,v)
  form.add_field("auth_key",settings.auth_key)
  form.add_file("file_data",fn,open(fn,"rb"))
  request=urllib2.Request(settings.url)
  body=str(form).encode('utf-8')
  request.add_header("Content-type", form.get_content_type())
  request.add_header("Content-length", len(body))  
  request.add_data(body)
  urllib2.urlopen(request).read()


if __name__=="__main__":
  import sys
  csvsource=sys.argv[1]
  for r in UnicodeDictReader(open(csvsource,"rb")):
    post_record(r)
