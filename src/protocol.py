# -*- encoding: utf-8 -*-
# $File: protocol.py
# $Date: 2012-2-29 下午4:35:25
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
import logging

# select suitable JSON library
#
# Here is the rough speed test of JSON libs
# http://j2labs.tumblr.com/post/4262756632/speed-tests-for-json-and-
# cpickle-in-python
#
CJSON = False
try:
    import cjson
    CJSON = True
except ImportError:
    import simplejson as json
    logging.info('Cjson is preferred to simplejson in speed.')

# For later extending, I choose JSON RPC to transport data between 
# controller and clients. However,  I didn't follow the JSON specification 
# exactly, in that I allow method call from server to client. Besides, I 
# assume the protocol is JSON RPC 2.0 without negotiation.
#

# Protocol Error
class Fault(Exception):
    def __init__(self, code, message, *args, **kwargs):
        Exception.__init__(self, *((code, message) + args), **kwargs)
        self.code = code
        self.message = message

(FAULT_SERVER_ERROR, FAULT_INVALID_JSON_RPC, FAULT_PROC_NOT_FOUND,  
 FAULT_PARAMS_INVALID, FAULT_PARSE_ERROR, ) = (
    (-32500, 'Internal server error.'), # Non-standard
    (-32600, 'Invalid JSON-RPC message.'),
    (-32601, 'Procedure not found.'),
    (-32602, 'Parameters invalid.'), # Non-standard
    (-32700, 'Parse error.'),
)

# Protocol parse
if (CJSON):
    json_encode = cjson.encode
    json_decode = cjson.decode
    JsonEncodeError = cjson.EncodeError
    JsonDecodeError = cjson.DecodeError
else:
    json_encode = json.dumps
    json_decode = json.loads
    JsonEncodeError = TypeError
    JsonDecodeError = json.JSONDecodeError

# Protocol Request
class Request(object):
    def __init__(self, method, params=None, id=None):
        '''
        Create a JSON RPC request object.
        
        :param method: JSON request method.
        :type method: unicode.
        
        :param params: JSON request parameters.
        :type params: A list, a tuple or a dict. Dict indicates that 
            the request uses named parameters.
            
        :param id: JSON request id.
        :type id: int.
        '''
        self.id = id
        self.method = method
        self.params = params
        
    def toJSON(self):
        '''Generate JSON RPC request string.'''
        try:
            obj = {'id': self.id, 'method': self.method}
            if (self.params is not None):
                obj['params'] = self.params
            return json_encode(obj)
        except JsonEncodeError:
            raise Fault(*FAULT_SERVER_ERROR)
        except Exception:
            raise Fault(*FAULT_SERVER_ERROR)
        
    @staticmethod
    def fromJSON(s):
        '''Make request from JSON RPC string.'''
        req = None
        try:
            req = json_decode(s)
        except JsonDecodeError:
            raise Fault(*FAULT_PARSE_ERROR)
        
        if (not isinstance(req, dict)):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        if ('id' not in req or 'method' not in req
                or req['method'] is None):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        if ('params' in req and
            (not isinstance(req['params'], dict)
                and not isinstance(req['params'], list)
                and not isinstance(req['params'], tuple))):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        
        return Request(req['method'], req.get('params', None), req['id'])
        
class Response(object):
    def __init__(self, result=None, error=None, id=None):
        '''
        Create a JSON RPC response object.
        
        :param result: JSON response result.
        :type result: anything.
        
        :param error: JSON response error.
        :type params: None or Fault.
        
        :param id: JSON response id.
        :type id: int.
        '''
        self.id = id
        self.result = result
        self.error = error
        
    def isError(self):
        return self.error is not None
        
    def toJSON(self):
        '''Generate JSON RPC response string.'''
        try:
            obj = {'id': self.id}
            if (self.error is not None):
                obj['error'] = {'code': self.error.code, 
                                'message': self.error.message}
            else:
                obj['result'] = self.result
            return json_encode(obj)
        except JsonEncodeError:
            raise Fault(*FAULT_SERVER_ERROR)
        except Exception:
            raise Fault(*FAULT_SERVER_ERROR)
        
    @staticmethod
    def fromJSON(s):
        '''Make response from JSON RPC string.'''
        req = None
        try:
            req = json_decode(s)
        except JsonDecodeError:
            raise Fault(*FAULT_PARSE_ERROR)
        
        if (not isinstance(req, dict)):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        if ('id' not in req):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        
        result = error = None
        if ('error' in req):
            error = req['error']
            if ('code' not in error or 'message' not in error):
                raise Fault(*FAULT_INVALID_JSON_RPC)
            error = Fault(error['code'], error['message'])
        else:
            result = req['result']
        
        return Response(result, error, req['id'])
    
# auto detect input is a request or a response
# and return the object
def parseJson(s):
    '''
    Make request or response from JSON RPC string.
    
    It the request string is like a request, and it is not valid, a tuple
    (Fault, id) will be returned to indicate the error. Otherwise, any 
    error input will get a None.
    '''
    ret = None
    m_id = None
    intend_to_be_request = False
    
    try:
        try:
            ret = json_decode(s)
        except JsonDecodeError:
            raise Fault(*FAULT_PARSE_ERROR)
        
        if (not isinstance(ret, dict)):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        if ('id' not in ret):
            raise Fault(*FAULT_INVALID_JSON_RPC)
        m_id = ret['id']
    
        # assume a request
        if ('method' in ret):
            intend_to_be_request = True
            if (ret['method'] is None or
                'params' in ret and
                (not isinstance(ret['params'], dict)
                    and not isinstance(ret['params'], list)
                    and not isinstance(ret['params'], tuple))):
                raise Fault(*FAULT_INVALID_JSON_RPC)
            return Request(ret['method'], ret.get('params', None), ret['id'])
    
        # assume a response
        result = error = None
        if ('error' in ret):
            error = ret['error']
            if ('code' not in error or 'message' not in error):
                raise Fault(*FAULT_INVALID_JSON_RPC)
            error = Fault(error['code'], error['message'])
        else:
            result = ret['result']
        
        return Response(result, error, ret['id'])
    except Fault as e:
        if (intend_to_be_request):
            return (e, m_id)
        return None

# Service object decorator
def expose(f, is_expose=True):
    setattr(f, '_json_rpc_exposed', is_expose)
    return f
    
def is_exposed(f):
    return (f is not None) and (getattr(f, '_json_rpc_exposed', False))
    
# Protocol Server
class Dispatcher(object):
    '''
    JSON RPC protocol dispatcher implement.
    
    The class provides a super class for JSON RPC dispatcher. Any class  
    providing a JSON RPC service can derive this class to implement RPC 
    methods or simply give a handler when create dispatcher.
    
    RPC methods should be decorated by protocol.expose.
    '''
    
    def __init__(self, handler=None):
        '''
        Create a JSON RPC dispatcher.
        
        :param handler: Method handler. None to use the dispatcher itself.
        :type handler: object.
        '''
        self.handler = handler if handler is not None else self
        
    def _call(self, method, *args, **kwargs):
        return method(*args, **kwargs)
        
#    def dispatch_raw(self, request):
#        '''
#        Dispatch the request and make result.
#        
#        :param request: Request JSON string.
#        :type request: unicode.
#        
#        :return str.
#        '''
#        req = None
#        try:
#            # parse request
#            req = Request.fromJSON(request)
#            # do dispatch
#            self.dispatch(req)
#        except Fault as fault:
#            # return error
#            return Response(None, fault, req.id if req is not None 
#                                                else None).toJSON()
                                                
    def dispatch(self, request):
        '''
        Dispatch the request and make result.
        
        :param request: JSON request.
        :type request: protocol.Request.
        
        :return Response.
        '''
        req = request
        try:
            # get method
            method = getattr(self.handler, req.method, None)
            if (not callable(method) or not is_exposed(method)):
                raise Fault(*FAULT_PROC_NOT_FOUND)
            # call method
            ret = None
            try:
                if (req.params is None):
                    ret = self._call(method)
                elif (isinstance(req.params, dict)):
                    ret = self._call(method, **req.params)
                else:
                    ret = self._call(method, *req.params)
            except TypeError:
                raise Fault(*FAULT_PARAMS_INVALID)
            except Exception:
                logging.exception('RPC method `%s` raised exception.'
                                   % req.method)
                raise Fault(*FAULT_SERVER_ERROR)
            # make result
            return Response(ret, None, req.id)
        except Fault as fault:
            # return error
            return Response(None, fault, req.id)
