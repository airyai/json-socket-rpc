# -*- encoding: utf-8 -*-
# $File: client.py
# $Date: 2012-3-2 下午5:12:26
#
# Copyright (C) 2012 the pynojo development team <see AUTHORS file>
# 
# Contributors to this file:
#    PWX    <airyai@gmail.com>
#
# This file is part of pynojo
# 
# pynojo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# pynojo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with pynojo.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function, unicode_literals
import session, protocol

import socket
import gevent.socket, gevent.ssl

# Client Session
class ClientSession(session.Session):
    '''Client-side socket session.'''
    def __init__(self, socket):
        super(ClientSession, self).__init__(socket)
        
    @protocol.expose
    def echo(self, message):
        return message

# Client 
class Client(object):
    '''Implement the RPC client.'''
    def __init__(self, address, sessionClass=ClientSession, **ssl_args):
        '''
        Create a client socket with remote server.
        '''
        self._sck = gevent.socket.create_connection(address)
        if (len(ssl_args)):
            self._sck = gevent.ssl.wrap_socket(self._sck, **ssl_args)
        self.SessionClass = sessionClass
        self.session = sessionClass(self._sck)
            
    def serve(self):
        '''Process client message loop.'''
        if (self.session is None):
            return
        self.session.serve()
        self.session.abandon()
        self.session = None
        self._sck = None
        
    def disconnect(self):
        '''Disconnect client.'''
        self.session.abandon()
        
    def call(self, method, *args, **kwargs):
        '''
        Call remote RPC method.
        
        JSON RPC requires only one of the list params or dict params,
        so pass *args and **kwargs at the same time will cause a 
        TypeError.
        
        Raise socket.error if the connection has been closed, and 
        gevent.timeout.Timeout when request timeout.
        '''
        if (self.session is None):
            return
        try:
            return self.session.call(method, *args, **kwargs)
        except socket.error:
            self.session.abandon()
            self._sck = self.session = None
            raise
    
    def broadcast(self, method, *args, **kwargs):
        '''
        Broadcast a RPC method call.
        
        The broadcast does not care about other clients' response. In 
        fact, the server just send back the number of living clients.
        
        Raise socket.error if the connection has been closed, and 
        gevent.timeout.Timeout when request timeout.
        '''
        if (len(args) > 0 and len(kwargs) > 0):
            raise TypeError('JSON RPC requires only one of the list '
                            'params or dict params.')
        params = {'method': method,
                  'params': args if len(args) > 0
                                 else kwargs if len(kwargs) > 0
                                             else None}
        return self.call('broadcast', params)
        
    def setRequestTimeout(self, timeout):
        '''Set request timeout.'''
        self.session.requestTimeout = timeout
        
    def getRequestTimeout(self):
        '''Get request timeout.'''
        return self.session.requestTimeout
        
