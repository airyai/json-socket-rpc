# -*- encoding: utf-8 -*-
# $File: session.py
# $Date: 2012-3-2 上午11:20:35
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
import protocol

import socket
import gevent.event, gevent.coros

class Session(protocol.Dispatcher):
    '''
    JSON RPC socket session (as well as RPC dispatcher).
    
    Manage RPC request list, and assign every request with a different 
    id, so that multiple requests can be made at one time correctly.
    '''
    def __init__(self, socket):
        '''
        Create a session.
        
        :param socket: The stream socket instance.
        :type socket: gevent.socket.socket.
        '''
        super(Session, self).__init__()
        self.peerName = socket.getpeername()
        self.name = ':'.join([str(s) for s in self.peerName[:2]])
        self._disp = self
        self._sck = socket
        self._fp = socket.makefile('r')
        self._lock = gevent.coros.Semaphore()
        self._requests = {}     # request queue
        self._requestId = 1     # manage request id
        self.requestTimeout = None # default request timeout
        
    def writeline(self, msg):
        '''
        Send a line of message to the socket.
        Nothing will be returned, but if the remote socket has closed, 
        Session._disconnected will be called.
        
        :param msg: Message body.
        :type msg: UTF-8 string.
        '''
        if (self._sck is None):
            return False
        ret = False
        try:
            self._sck.sendall(msg + '\n')
            ret = True
        except socket.error:
            self._disconnected()
        return ret
        
    def readline(self):
        '''
        Read a line of message from the socket.
        
        If socket has been closed, an empty string will be returned.
        '''
        if (self._fp is None):
            return ''
        ret = self._fp.readline()
        if (not ret):
            self._disconnected()
        return ret
    
    def _disconnected(self):
        '''Callback when the socket has been disconnected.'''
        # unset all objects
        if (self._fp is not None):
            self._fp.close()    # TODO: test if .close blocks!
            self._fp = None
        if (self._sck is not None):
            self._sck.close()
            self._sck = None
        # abandon all request
        events = {}
        events.update(self._requests)
        self._requests.clear()
        for e in events.itervalues():
            e.set_exception(socket.error('Connection closed.'))
            
    def abandon(self):
        '''Abandon the session.'''
        #self._sck.close()
        self._disconnected()
        
    def serve(self):
        '''Start socket messge loop.'''
        while self._sck is not None:
            msg = self.readline()
            if (not msg):
                return
            msg = msg.strip()
            obj = protocol.parseJson(msg)
            if (isinstance(obj, tuple)):
                self._send_response(protocol.Response(None, obj[0], obj[1]))
            elif (isinstance(obj, protocol.Response)):
                self._got_response(obj)
            elif (isinstance(obj, protocol.Request)):
                gevent.spawn(self._serve_request, obj)
            else:
                self._got_badmessage(msg)
                
    def _got_badmessage(self, msg):
        '''Called while socket received a bad message.'''
        pass
                
    def _send_response(self, response, asyncResult):
        '''Send response to the remote side.'''
        if (not self.writeline(response.toJSON())):
            asyncResult.set_exception(socket.error('Connection closed.'))

    def _serve_request(self, request):
        '''Serve when get request from remote side.'''
        result = self._disp.dispatch(request)
        self.writeline(result.toJSON())
        
    def _got_response(self, response):
        '''Parse the response from remote side.'''
        rId = response.id
        ev = self._requests.pop(rId, None)
        if (ev is not None):
            if (response.error is not None):
                ev.set_exception(response.error)
            else:
                ev.set(response.result)
    
    def _nextRquestId(self):
        '''get next available job id.'''
        self._lock.acquire()
        ret = self._requestId
        self._requestId += 1
        if (self._requestId == 0xffffffff):
            self._requestId = 1
        self._lock.release()
        return ret
    
    def doRequest(self, request, timeout=None):
        '''
        Emit a request.
        
        Raise socket.error if the connection has been closed.
        '''
        # serialize request
        s = request.toJSON()
        # assign a job id.
        rId = self._nextRquestId()
        request.id = rId
        result = gevent.event.AsyncResult()
        self._requests[rId] = result
        # emit job
        gevent.spawn(self._send_response, s, result)
        # wait for result & delete job
        try:
            ret = result.get(timeout=timeout)
            return ret
        except:
            self._requests.pop(rId, None)
            raise
        
    def call(self, method, *args, **kwargs):
        '''
        A fast interface to emit request.
        
        JSON RPC requires only one of the list params or dict params,
        so pass *args and **kwargs at the same time will cause a 
        TypeError.
        
        Raise socket.error if the connection has been closed.
        '''
        if (len(args) > 0 and len(kwargs) > 0):
            raise TypeError('JSON RPC requires only one of the list '
                            'params or dict params.')
        params = (args if len(args) > 0
                       else kwargs if len(kwargs) > 0
                                   else None)
        timeout = self.requestTimeout
        return self.doRequest(protocol.Request(method, params), timeout)
