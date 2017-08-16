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
import io
import pytest

import tomcatmanager as tm


class TestManagerBase:
    """base class for all tests with some convenience methods"""

    def success_assertions(self, r):
        """a set of common assertions for every command to ensure it
        completed successfully"""
        assert r.status_code == tm.codes.ok, 'message from server: "{}"'.format(r.status_message)
        assert r.status_message != None
        assert len(r.status_message) > 0
        r.raise_for_status()

    def failure_assertions(self, r):
        assert r.status_code == tm.codes.fail
        with pytest.raises(tm.TomcatError):
            r.raise_for_status()

    def info_assertions(self, r):
        """a set of common assertions that should be true of the info
        type commands which return a result"""
        self.success_assertions(r)
        assert r.result != None
        assert len(r.result) > 0    


class TestManager(TestManagerBase):

    ###
    #
    # is_stream
    #
    ###
    def test_is_stream_fileobj(self, localwar_file):
        with open(localwar_file, 'rb') as localwar_fileobj:
            assert tm.TomcatManager()._is_stream(localwar_fileobj)
    
    def test_is_stream_bytesio(self):
        fileobj = io.BytesIO(b'the contents of my warfile')
        assert tm.TomcatManager()._is_stream(fileobj)
        
    def test_is_stream_primitives(self):
        assert tm.TomcatManager()._is_stream(None) == False
        assert tm.TomcatManager()._is_stream('some string') == False
        assert tm.TomcatManager()._is_stream(['some', 'list']) == False

    ###
    #
    # init
    #
    ###
    def test_init_no_url(self, tomcat_manager_server):
        tomcat = tm.TomcatManager()
        assert tomcat.is_connected == False

    def test_init_noauth(self, tomcat_manager_server):
        tomcat = tm.TomcatManager(tomcat_manager_server['url'])
        assert tomcat.is_connected == False

    def test_init_auth(self, tomcat_manager_server):
        tomcat = tm.TomcatManager(
            tomcat_manager_server['url'],
            tomcat_manager_server['userid'],
            tomcat_manager_server['password'] )
        assert tomcat.is_connected == True

    ###
    #
    # connect
    #
    ###
    def test_connect_no_url(self, tomcat_manager_server):
        tomcat = tm.TomcatManager()
        with pytest.raises(requests.exceptions.MissingSchema):
            r = tomcat.connect()

    def test_connect_noauth(self, tomcat_manager_server):
        tomcat = tm.TomcatManager()
        r = tomcat.connect(tomcat_manager_server['url'])
        assert isinstance(r, tm.models.TomcatManagerResponse)
        assert tomcat.is_connected == False
        with pytest.raises(requests.exceptions.HTTPError):
            r.raise_for_status()

    def test_connect_auth(self, tomcat_manager_server):
        tomcat = tm.TomcatManager()
        r = tomcat.connect(
            tomcat_manager_server['url'],
            tomcat_manager_server['userid'],
            tomcat_manager_server['password'] )
        assert isinstance(r, tm.models.TomcatManagerResponse)
        assert r.status_code == tm.codes.ok
        assert tomcat.is_connected == True
        assert r.result == ''
        assert r.status_message == ''
        r.raise_for_status()        
