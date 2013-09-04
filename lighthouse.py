# 
#  lighthouse.py
#  Python Lighthouse API
#
#  Lighthouse simple hosted issue tracking, bug tracking, and project
#   management software.
#
#  They also have an XML-based API for working with your projects
#  
#  http://lighthouseapp.com
#  http://lighthouseapp.com/api
#
#  Created by Clinton Ecker on 2009-01-31.
#  Copyright 2009 Clint Ecker. All rights reserved.
# 
# //////////////////////////////////////////////////////////////////////
# 
#  Modified Version by Kjuly ( Kj Yu )
#  Author URL : http://kjuly.com
#
#  Description: 
#    It's modified and used for DevStats Project( thePlant Co. Ltd. )
#
#  Added Funs:
#    User
# 
import urllib2
from urllib2 import HTTPError
import os.path
from xmltodict import xmltodict


class Lighthouse(object):
    """The main lighthouse object for managing the connection"""
    
    def __init__(self, token=None, url=None):
        self.token = token
        self.url = url
        self._projects = None
        self.user = User()

    @property
    def projects(self):
        """Lazy-load projects once"""
        if self._projects is None:
            self._projects = self.get_projects()
        return self._projects

    def get_project(self, name):
        try:
            return (p for p in self.projects
                    if p.name == name or p.id == name or str(p.id) == name).next()
        except StopIteration:
            return None

    def _get_data(self, path):
        """Takes a path, joins it with the project's URL and grabs that 
        resource's XML data
        
        >>> lh = Lighthouse()
        >>> lh._get_data('projects.xml')
        Traceback (most recent call last):
        ...
        ValueError: Please set url properly
        >>> lh.url = 'http://ars.lighthouseapp.com'
        >>> lh._get_data('projectx.xml')
        Traceback (most recent call last):
        ...
        ExpatError: mismatched tag: line 30, column 4
        >>> lh.url = 'http://example.com'
        >>> lh._get_data('projects.xml')
        Traceback (most recent call last):
        ...
        HTTPError: HTTP Error 404: Not Found
        """
        if self.url != None:
            endpoint = os.path.join(self.url, path)
            req = urllib2.Request(endpoint)
            if self.token:
                req.add_header('X-LighthouseToken', self.token)
            resp = urllib2.urlopen(req)
            data = resp.read()
            return parse_xml(data)
        else:
            raise ValueError('Please set url properly')
    
    def _post_data(self, path, data):
        if self.url == None:
            raise ValueError('Please set url properly')
        if self.token == None:
            raise ValueError('Please set token properly')
        endpoint = os.path.join(self.url, path)
        headers = { 
            'Content-Type' : 'application/xml',
            'X-LighthouseToken' : self.token,
        }
        req = urllib2.Request(endpoint, data, headers)
        try:
            response = urllib2.urlopen(req)
        except HTTPError, response:
            if response.code == 201:
                data = response.read()
            else:
                raise
        else:
            data = response.read()
        return parse_xml(data)
            
    def fetch_members(self) :
        for p in self.projects :
            self.get_members( p ) # Get Members
        return

    def fetch_tickets(self) :
        """Pulls in all the tickets available and populates them with
        their properties"""
        for p in self.projects :
            self.get_tickets( p )
        return

    def fetch_all_tickets(self, page_start, page_end) :
        """Pulls in all the tickets available and populates them with
        their properties"""
        for p in self.projects :
            self.get_all_tickets( p, page_start, page_end )
        return

    def get_projects(self):
        """Retrieves all available projects
        
        >>> lh = Lighthouse()
        >>> lh.url = 'http://ars.lighthouseapp.com'
        >>> project = lh.projects[0]
        >>> len(lh.projects)
        1
        >>> project.name
        'Ars Technica 5.0'
        """
        path = Project.endpoint
        project_list = self._get_data(path)
        projects = []
        for project in project_list.get('children', ()):
            p = Project()
            for field in project['children']:
                field_name, field_value, field_type = parse_field(field)
                setattr(p, field_name.replace('-', '_'), field_value)
            projects.append(p)
        return projects

    def get_all_tickets(self, project, page_start, page_end):
        """Populates the project with all existing tickets
        
        >>> lh = Lighthouse()
        >>> lh = Lighthouse()
        >>> lh.url = 'http://ars.lighthouseapp.com'
        >>> project = lh.projects[0]
        >>> lh.get_all_tickets(project)
        
        >>>
        """
        c = 30
        page = page_start
        ticket_count = 0
        while c == 30 and page < page_end :
            c = self.get_tickets(project, page)
            ticket_count += c
            page += 1
        
    def get_tickets(self, project, page=1):
        """Retrieves all the tickets in a project
        
        >>> lh = Lighthouse()
        >>> lh.url = 'http://ars.lighthouseapp.com'
        >>> project = lh.projects[0]
        >>> lh.get_tickets(project)
        30
        >>> lh.get_tickets(project, 2)
        30
        >>> lh.get_tickets(project, 1000)
        0
        >>> lh.get_tickets(project, 0)
        Traceback (most recent call last):
        ...
        ValueError: Page number should be 1-indexed
        >>> lh.get_tickets(project, -1)
        Traceback (most recent call last):
        ...
        ValueError: Page number should be 1-indexed
        >>> lh.get_tickets(project, '1')
        Traceback (most recent call last):
        ...
        TypeError: Page number should be of type Integer
        >>> lh.get_tickets(123)
        Traceback (most recent call last):
        ...
        TypeError: Project must be instance of Project object
        >>> lh.get_tickets('project')
        Traceback (most recent call last):
        ...
        TypeError: Project must be instance of Project object
        """
        if not isinstance(project, Project):
            raise TypeError('Project must be instance of Project object')
        if not isinstance(page, int):
            raise TypeError('Page number should be of type Integer')
        if page <= 0:
            raise ValueError('Page number should be 1-indexed')
        path = Ticket.endpoint % (project.id)
        ticket_list = self._get_data(path+"?page=" + str(page))
        c = 0
        if(ticket_list.get('children', None)):
            for ticket in ticket_list['children']:
                c += 1
                if( ticket.get('children', None) ): # Got the KeyError 'children', so check whether it exists
                    t_obj = Ticket()
                    for field in ticket['children']:
                        field_name, field_value, field_type = \
                            parse_field(field)
                        py_field_name = field_name.replace('-', '_')
                        t_obj.__setattr__(py_field_name, field_value)
                        t_obj.fields.add(py_field_name)
                    project.tickets[t_obj.number] = t_obj
        return c

    def get_full_ticket(self, project, ticket):
        path = Ticket.endpoint_single % (project.id, ticket.number)
        ticket_data = self._get_data(path)

        for field in ticket_data['children']:
            field_name, field_value, field_type = parse_field(field)
            py_field_name = field_name.replace('-', '_')
            ticket.__setattr__(py_field_name, field_value)
            ticket.fields.add(py_field_name)

        return ticket
            
    def get_user( self ) :
        """Retrieves the tokens
        """
        path    = User.endpoint_token % ( self.token )
        token   = self._get_data( path )

        if( token.get('children', None) ) :
            for field in token['children'] :
                #m_obj = User()
                field_name, field_value, field_type = parse_field(field)
                py_field_name = field_name.replace('-', '_')
                self.user.__setattr__( py_field_name, field_value )
                self.user.fields.add( py_field_name )
            #project.user.append( m_obj )
            #self.user = m_obj

    def get_members( self, project ) :
        """Retrieves all the members in a project
        """
        if not isinstance(project, Project):
            raise TypeError('Project must be instance of Project object')

        path = Member.endpoint_proj % ( project.id )
        member_list = self._get_data( path ) # Has page or not ?

        if( member_list.get('children', None) ) :
            for member in member_list['children'] :
                m_obj = Member()
                for field in member['children']:
                    field_name, field_value, field_type = parse_field(field)
                    # Deep into sub level
                    if( field.get('children', None) ) :
                        set_sub = {}
                        for field_sub in field['children'] :
                            field_name_s, field_value_s, field_type_s = parse_field(field_sub)
                            py_field_name_s = field_name_s.replace('-', '_')
                            set_sub[ py_field_name_s ] = field_value_s
                        m_obj.__setattr__( field_name, set_sub )
                        m_obj.fields.add( field_name )

                    else :
                        py_field_name = field_name.replace('-', '_')
                        m_obj.__setattr__( py_field_name, field_value )
                        m_obj.fields.add( py_field_name )
                project.members.append( m_obj )

    def add_ticket(self, project=None, title=None, body=None):
        if project is None:
            project = self.projects[0]
            project_id = project.id
        elif isinstance(project, Project):
            project_id = project.id
        else:
            project = self.get_project(project)
            project_id = project.id
            if project is None:
                raise ValueError('Couldn\'t find a project matching \''+project+'\'')
        path = Ticket.endpoint % (project_id,)
        data = Ticket.creation_xml % {
            'body':body, 
            'title':title,
        }
        new_ticket = self._post_data(path, data)
        t_obj = Ticket()
        for field in new_ticket['children']:
            field_name, field_value, field_type = parse_field(field)
            t_obj.__setattr__(field_name.replace('-', '_'),\
                field_value)
        return t_obj
    
class Ticket(object):
    """Tickets are individual issues or bugs"""
    
    endpoint = 'projects/%d/tickets.xml'
    endpoint_single = 'projects/%d/tickets/%d.xml'
    creation_xml = """<ticket>
    <body>%(body)s</body>
    <title>%(title)s</title>
</ticket>"""
    def __init__(self):
        super(Ticket, self).__init__()
        self.versions = []
        self.attachments = []
        self.fields = set()
        
    def __repr__(self):
        if self.title:
            return "Ticket: %s" % (self.title,)
        else:
            return "Ticket: Unnamed"
        
    def to_json_obj(self):
        return dict([(f, getattr(self, f)) for f in self.fields])
    
class Project(object):
    """Projects contain milestones, tickets, messages, and changesets"""
    
    endpoint = 'projects.xml'
    
    def __init__(self):
        super(Project, self).__init__()
        self.tickets = {}
        self.members = []   # Members
        self.milestones = []
        self.messages = []
        self.name = None

    def __repr__(self):
        return "Project: %s" % (self.name or 'Unnamed',)


class Milestone(object):
    """Milestones reference tickets"""
    def __init__(self, arg):
        super(Milestone, self).__init__()
        self.arg = arg
        
class Message(object):
    """Messages are notes"""
    def __init__(self, arg):
        super(Message, self).__init__()
        self.arg = arg
        
class Member(object):
    """A Member"""
    endpoint_proj = 'projects/%d/memberships.xml'
    endpoint_user = 'users/%d/memberships.xml'

    def __init__( self ) :
        super( Member, self ).__init__()
        self.fields = set()

class User(object):
    """A user"""
    endpoint_token  = 'tokens/%s.xml'
    endpoint_user   = 'users/%d.xml'

    def __init__( self ):
        super(User, self).__init__()
        self.fields = set()


def parse_field(field):
    field_type = None

    attributes = field.get('attributes', {})
    field_value = field.get('cdata', None)
    field_name = field.get('name', None)

    if attributes:
        field_type = attributes.get('type', None)

    if field_type == "array":
        field_value = parse_array(field)

    elif field_type and (field_value is not None):
        if field_type == "datetime" :
            field_value = str(field_value)
        else :
            converter = __module_locals.get('parse_' + field_type)
            field_value = converter(field_value)

    return field_name, field_value, field_type


def parse_array(data):
    """Returns an array """
    r = []
    for item in data['children']:
        item_obj = {}
        for field in item['children']:
            field_name, field_value, field_type = parse_field(field)
            item_obj[field_name.replace('-', '_')] = field_value
        r.append(item_obj)
    return r


parse_string = str

parse_yaml = parse_string

parse_nil = lambda: None


def parse_boolean(data):
    return data in ('true', 'True', '1', 1)


def parse_integer(data):
    return int(data, 10) if data else None


def parse_xml(xmldata):
    return xmltodict(xmldata)


__module_locals = locals()


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
