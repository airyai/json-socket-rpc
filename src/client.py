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
import session

# Client Session
class ClientSession(session.Session):
    '''Client-side socket session.'''
    def __init__(self, socket):
        super(ClientSession, self).__init__(socket)

# Client 
class Client(object):
    '''Implement the RPC client.'''
    pass
