# -*- encoding: utf-8 -*-
# $File: server.py
# $Date: 2012-2-29 下午4:25:14
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
from gevent.server import StreamServer
import logging

import session
import protocol
import time

# Server Session
class ServerSession(session.Session):
    '''Server-side socket session.'''
    def __init__(self, server, socket):
        super(ServerSession, self).__init__(socket)
        self.server = server

    @protocol.expose
    def broadcast(self, call):
        '''Broadcast RPC call to all clients connected.'''
        method_call = call
        method = params = None
        if (isinstance(method_call, dict)):
            method = method_call.get('method', None)
            params = method_call.get('params', None)
        elif (isinstance(method_call, tuple) or 
                isinstance(method_call, list)):
            if (len(method_call) >= 2):
                method = method_call[0]
                params = method_call[1]
        if (method is None or (params is not None
                                 and not isinstance(params, dict)
                                 and not isinstance(params, tuple)
                                 and not isinstance(params, list))):
            raise TypeError()
        req = protocol.Request(method, params)
        return self.server.broadcast(self, req)
    
    @protocol.expose
    def echo(self, message):
        return message
        
    def _got_badmessage(self, msg):
        '''On bad message received.'''
        self.writeline(protocol.Response(error=
                          protocol.Fault(*protocol.FAULT_INVALID_JSON_RPC)
                    ).toJSON())
        self.abandon()
    
# RPC server
class Server(StreamServer):
    '''Implement the RPC server.'''
    
    def __init__(self, listener, sessionClass=ServerSession, backlog=None, 
                 spawn='default', verbose=False, **ssl_args):
        '''
        Create a new RPC server.
        
        :param listener: Tuple (address, port).
        :type listener: tuple.
        :param sessionClass: The class of Session.
        :type sessionClass: Derived class of ServerSession.
        '''
        StreamServer.__init__(self, listener, self._handle, backlog,
                              spawn, **ssl_args)
        self.SessionClass = sessionClass
        self.clients = {}
        self.verbose = verbose
        
    def _handle(self, socket, address):
        '''Handle the session of a socket.'''
        
        session = self.SessionClass(self, socket)
        logging.debug('Client %s connected.' % session.name)
        
        self.clients[session] = time.time()
        session.serve()
        session.abandon()
        del self.clients[session]
        
        logging.debug('Client %s disconnected.' % session.name)
        
    def broadcast(self, session, call):
        '''
        Send a RPC call to all clients.
        
        :return: Successful count.
        '''
        message = call.toJSON()
        if (self.verbose):
            logging.debug('Broadcast from %s: %s.' % (session.name, message))
        else:
            logging.debug('Broadcast from %s.' % (session.name))
            
        message = str(message)
        
        clients = list(self.clients.keys())
        success = 0
        for c in clients:
            if (c == session):
                continue
            # Just broadcast, did not expect a result
            # If result, ignore it.
            if (c.writeline(message)):
                success += 1
        del clients
        return success


