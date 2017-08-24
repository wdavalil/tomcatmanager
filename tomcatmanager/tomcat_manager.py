#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import requests
import collections

from .models import codes, TomcatManagerResponse, ServerInfo


class TomcatManager:
    """
    A class for interacting with the Tomcat Manager web application.
    
    
    Here's a summary of the recommended way to use this class with proper
    exception and error handling. For this example, we'll use the
    `server_info()` method.
    
    >>> import tomcatmanager as tm
    >>> url = 'http://localhost:8080/manager'
    >>> user = 'ace'
    >>> password = 'newenglandclamchowder'
    >>> 
    >>> tomcat = tm.TomcatManager()
    >>> try:
    ...     r = tomcat.connect(url, user, password)
    ...     if r.ok:
    ...         r = tomcat.server_info()
    ...         if r.ok:
    ...             print(r.server_info)
    ...         else:
    ...             print('Error: {}'.format(r.status_message))
    ...     else:
    ...         print('Error: not connected')
    ... except Exception as err:
    ...     # handle exception
    ...     print('Error: not connected')
    Error: not connected

    """

    @classmethod
    def _is_stream(self, obj):
        """return True if passed a stream type object"""
        return all([
            hasattr(obj, '__iter__'),
            not isinstance(obj, (str, bytes, list, tuple, collections.Mapping))
        ])
        
    def __init__(self):
        """
        Initialize a new TomcatManager object.
        """
        self._url = None
        self._user = None
        self._password = None
        
        self.timeout = 15

    def _get(self, cmd, payload=None):
        """
        Make an HTTP get request to the tomcat manager web app.
        
        :return: `TomcatManagerResponse` object
        """
        base = self._url or ''
        # if we have no _url, don't add other stuff to it because it makes
        # the exceptions hard to understand
        if base:
            url = base + '/text/' + cmd
        else:
            url = ''
        r = TomcatManagerResponse()
        r.response = requests.get(
                url,
                auth=(self._user, self._password),
                params=payload,
                timeout=self.timeout,
                )
        return r

    ###
    #
    # convenience and utility methods
    #
    ###
    def connect(self, url, user=None, password=None):
        """
        Connect to a Tomcat Manager server.
        
        :param url:      url where the Tomcat Manager web application is
                         deployed
        :param user:     (optional) user to authenticate with
        :param password: (optional) password to authenticate with
        :return:         `TomcatManagerResponse` object
        
        You don't have to connect before using any other commands. If you
        initialized the object with credentials you can call any other
        method. The purpose of `connect()` is to:
        
        - give you a way to change the credentials on an existing object
        - provide a convenient mechanism to validate you can actually
          connect to the server
        - allow you to inspect the response so you can see why you can't connect
        
        Usage:
        
        >>> import tomcatmanager as tm
        >>> url = 'http://localhost:8080/manager'
        >>> user = 'ace'
        >>> password = 'newenglandclamchowder'
        >>> 
        >>> tomcat = tm.TomcatManager()
        >>> try:
        ...     r = tomcat.connect(url, user, password)
        ...     if r.ok:
        ...         print('connected')
        ...     else:
        ...         print('not connected')
        ... except Exception as err:
        ...     # handle exception
        ...     print('not connected')
        not connected
                
        The only way to validate whether we are connected is to actually
        get a url. Internally this method tries to retrieve
        ``/manager/text/serverinfo``.
        
        Requesting url's via http can raise all kinds of exceptions. For
        example, if you give a URL where no web server is listening, you'll
        get a `requests.connections.ConnectionError`. However, this
        method won't raise exceptions for everything. If the credentials
        are incorrect, you won't get an exception unless you ask for it.
        
        You can also use `is_connected()` to check if you are connected.
        
        If you want to raise more exceptions see
        `TomcatManagerResponse.raise_for_status()`.
        
        """
        self._url = url
        self._user = user
        self._password = password
        r = self._get('serverinfo')
        
        if not r.ok:
            # don't save the parameters if we don't succeed
            self._url = None
            self._user = None
            self._password = None
        # hide the fact that we retrieved results, we don't
        # want people relying on or using this data
        r.result = ''
        r.status_message = ''
        return r

    @property
    def is_connected(self):
        """
        Does the url point to an actual tomcat server and are the credentials valid?
        
        :return: True if connected to a tomcat server, otherwise, False
        """
        try:
            r = self._get('list')
            return r.ok
        except:
            return False

    ###
    #
    # managing applications
    #
    ###
    def deploy(self, path, localwar=None, serverwar=None, version=None, update=False):
        """
        Deploy an application to the Tomcat server.
        
        If the WAR file is already present somewhere on the same server
        where Tomcat is running, you should use the ``serverwar`` parameter. If
        the WAR file is local to where python is running, use the ``localwar``
        parameter. Specify either ``localwar`` or ``serverwar``, but not both. 
        
        :param path:         The path on the server to deploy this war to,
                             i.e. /sampleapp
        :param localwar:     (optional) The path (specified using your
                             particular operating system convention) to a war
                             file on the local file system. This will be sent
                             to the server for deployment.
        :param serverwar:    (optional) The java-style path (use slashes not
                             backslashes) to the war file on the server. Don't
                             include ``file:`` at the beginning.
        :param version:      (optional) For tomcat parallel deployments, the
                             version string to associate with this version
                             of the app
        :param update:       (optional) Whether to undeploy the existing path
                             first (default False)
        :return:             `TomcatManagerResponse` object
        :raises ValueError:  if no path is specified;
                             if both `localwar` and `serverwar` are given;
                             if neither `localwar` or `serverwar` are given
        """
        params = {}
        if path:
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if update:
            params['update'] = 'true'
        if version:
            params['version'] = version

        if localwar and serverwar:
            raise ValueError('can not deploy localwar and serverwar at the same time')
        elif localwar:
            # PUT a local stream
            base = self._url or ''
            url = base + '/text/deploy'
            if self._is_stream(localwar):
                warobj = localwar
            else:
                warobj = open(localwar, 'rb')   

            r = TomcatManagerResponse()
            r.response = requests.put(
                    url,
                    auth=(self._user, self._password),
                    params=params,
                    data=warobj,
                    timeout=self.timeout,
                    )
        elif serverwar:
            params['war'] = serverwar
            r = self._get('deploy', params)
        else:
            raise ValueError('neither localwar or serverwar specified: nothing to deploy')

        return r

    def undeploy(self, path, version=None):
        """Undeploy the application at a given path.
        
        :param path:         The path of the application to undeploy
        :param version:      (optional) The version string of the app to
                             undeploy
        :return:             `TomcatManagerResponse` object
        :raises ValueError:  if no path is specified
        
        If the application was deployed with a version string, it must be
        specified in order to undeploy the application.
        """
        params = {}
        if path:
            params = {'path': path}
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        return self._get('undeploy', params)

    def start(self, path, version=None):
        """
        Start the application at a given path.
    
        :param path:         The path of the application to start
        :param version:      (optional) The version string of the app to start
        :return:             `TomcatManagerResponse` object
        :raises ValueError:  if no path is specified
        
        If the application was deployed with a version string, it must be
        specified in order to start the application.
        """
        params = {}
        if path:
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        return self._get('start', params)

    def stop(self, path, version=None):
        """
        Stop the application at a given path.
    
        :param path:         The path of the application to stop
        :param version:      (optional) The version string of the app to stop
        :return:             `TomcatManagerResponse` object
        :raises ValueError:  if no path is specified
        
        If the application was deployed with a version string, it must be
        specified in order to stop the application.
        """
        params = {}
        if path:
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        return self._get('stop', params)

    def reload(self, path, version=None):
        """
        Reload (stop and start) the application at a given path.
        
        :param path:         The path of the application to reload
        :param version:      (optional) The version string of the app to reload
        :return:             `TomcatManagerResponse` object
        :raises ValueError:  if no path is specified
                
        If the application was deployed with a version string, it must be
        specified in order to reload the application.
        """
        params = {}
        if path:
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        return self._get('reload', params)

    def sessions(self, path, version=None):
        """
        Get the age of the sessions in an application.

        :param path:         The path of the application to get session
                             information about
        :param version:      (optional) The version string of the app to get
                             session information about
        :return:             `TomcatManagerResponse` object with the session
                             summary in both the ``result`` attribute and the
                             ``sessions`` attribute
        :raises ValueError:  if no path is specified
    
        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.sessions('/manager')
            >>> if r.ok:
            ...     session_data = r.sessions

        """
        params = {}
        if path:
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        r = self._get('sessions', params)
        if r.ok:
            r.sessions = r.result
        return r

    def expire(self, path, version=None, idle=None):
        """
        Expire sessions idle for longer than idle minutes.
        
        :param path:         the path to the app on the server whose
                             sessions you want to expire
        :param idle:         sessions idle for more than this number of
                             minutes will be expired. Use idle=0 to expire
                             all sessions.
        :return:             `TomcatManagerResponse` with the session
                             summary in the ``result`` attribute and in
                             the ``sessions`` attribute
        :raises ValueError:  if no path is specified
        
        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.expire('/manager', idle=15)
            >>> if r.ok:
            ...     expiration_data = r.sessions
        """
        params = {}
        if path:        
            params['path'] = path
        else:
            raise ValueError('no path specified')
        if version:
            params['version'] = version
        if idle:
            params['idle'] = idle       
        r = self._get('expire', params)
        if r.ok:
            r.sessions = r.result
        return r

    def list(self):
        """
        Get a list of all applications currently installed.

        :return: `TomcatManagerResponse` object with an additional
                 ``apps`` attribute
        
        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.list()
            >>> if r.ok:
            ...     running = []
            ...     for (path, status, sessions, dir) in r.apps:
            ...         if status == 'running': running.append(path)        
        
        ``apps`` is a list of tuples: (``path``, ``status``, ``sessions``, ``directory``)
        
        * ``path`` - the relative URL where this app is deployed on the server
        * ``status`` - whether the app is running or not
        * ``sessions`` - number of currently active sessions
        * ``directory`` - the directory on the server where this app resides    
        """
        r = self._get('list')
        apps = []
        for line in r.result.splitlines():
            apps.append(line.rstrip().split(":"))       
        r.apps = apps
        return r

    ###
    #
    # These commands return info about the server
    #
    ###
    def server_info(self):
        """
        Get information about the Tomcat server.
        
        :return: `TomcatManagerResponse` object with an additional
                 ``server_info`` attribute

        The ``server_info`` attribute contains a `ServerInfo` object, which is
        a dictionary with some added properties for well-known values
        returned from the Tomcat server.
        
        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.server_info()
            >>> if r.ok:
            ...     r.server_info['OS Name'] == r.server_info.os_name
            True

        """
        r = self._get('serverinfo')
        r.server_info = ServerInfo(r.result)
        return r

    def status_xml(self):
        """
        Get server status information in XML format.

        :return: `TomcatManagerResponse` object with an additional
                 ``status_xml`` attribute

        Usage::

            >>> import xml.etree.ElementTree as ET
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.status_xml()
            >>> if r.ok:
            ...     root = ET.fromstring(r.status_xml)
            ...     mem = root.find('jvm/memory')
            ...     print('Free Memory = {}'.format(mem.attrib['free'])) #doctest: +ELLIPSIS
            Free Memory ...

        Tomcat 8.0 doesn't include application info in the XML, even though the docs
        say it does.
        """
        # this command isn't in the /manager/text url space, so we can't use _get()
        base = self._url or ''      
        url = base + '/status/all'
        r = TomcatManagerResponse()
        r.response = requests.get(
                url,
                auth=(self._user, self._password),
                params={'XML': 'true'},
                timeout=self.timeout,
                )
        r.result = r.response.text
        r.status_xml = r.result

        # we have to force a status_code and a status_message
        # because the server doesn't return them
        if r.response.status_code == requests.codes.ok:
            r.status_code = codes.ok
            r.status_message = codes.ok
        else:
            r.status_code = codes.fail
            r.status_message = codes.fail
        return r

    def vm_info(self):
        """
        Get diagnostic information about the JVM.
                
        :return: `TomcatManagerResponse` object with an additional
                 ``vm_info`` attribute
        """
        r = self._get('vminfo')
        r.vm_info = r.result
        return r

    def ssl_connector_ciphers(self):
        """
        Get SSL/TLS ciphers configured for each connector.

        :return: `TomcatManagerResponse` object with an additional
                 ``ssl_connector_ciphers`` attribute
        """
        r = self._get('sslConnectorCiphers')
        r.ssl_connector_ciphers = r.result
        return r

    def thread_dump(self):
        """
        Get a jvm thread dump.

        :return: `TomcatManagerResponse` object with an additional
                 ``thread_dump`` attribute
        """
        r = self._get('threaddump')
        r.thread_dump = r.result
        return r

    def resources(self, type=None):
        """
        Get the global JNDI resources available for use in resource links for context config files
        
        :param type: (optional) fully qualified java class name of the
                     resource type you are interested in. For example,
                     pass ``javax.sql.DataSource`` to acquire the names
                     of all available JDBC data sources.
        :return:     `TomcatManagerResponse` object with an additional
                     ``resources`` attribute


        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.resources()
            >>> if r.ok:
            ...     print(r.resources)
            {'UserDatabase': 'org.apache.catalina.users.MemoryUserDatabase'}       
        
        ``resources`` is a dictionary with the resource name as the key
        and the class name as the value        
        """
        if type:
            r = self._get('resources', {'type': str(type)})
        else:
            r = self._get('resources')

        resources = {}
        for line in r.result.splitlines():
            resource, classname = line.rstrip().split(':',1)
            if resource[:7] != codes.fail + ' - ':
                resources[resource] = classname.lstrip()
        r.resources = resources
        return r


    def find_leakers(self):
        """
        Get apps that leak memory.
        
        :return: `TomcatManagerResponse` object with an additional
                 ``leakers`` attribute
        
        The ``leakers`` attribute contains a list of paths of applications
        which leak memory.
        
        This command triggers a full garbage collection on the server. Use with
        extreme caution on production systems.
        
        Explicity triggering a full garbage collection from code is documented to be
        unreliable. Furthermore, depending on the jvm, there are options to disable
        explicit GC triggering, like ```-XX:+DisableExplicitGC```. If you want to make
        sure this command triggered a full GC, you will have to verify using something
        like GC logging or JConsole.

        The Tomcat Manager documentation says the server can return duplicates in this
        list if the app has been reloaded and was leaking both before and after the
        reload. The list returned by the ``leakers`` attribute will have no duplicates in
        it.

        Usage::
        
            >>> tomcat = getfixture('tomcat')
            >>> r = tomcat.find_leakers()
            >>> if r.ok:
            ...     cnt = len(r.leakers)
            ... else:
            ...     cnt = 0
        """
        r = self._get('findleaks', {'statusLine': 'true'})
        r.leakers = self._parse_leakers(r.result)
        return r

    def _parse_leakers(self,text):
        """
        Parse a list of leaking apps from the text returned by tomcat.
        
        We use this as a separate method so that we can test it against
        several data sets to ensure proper behavior.
        """
        leakers = []
        for line in text.splitlines():
            # don't add duplicates
            if not line in leakers:
                leakers.append(line)
        return leakers
        