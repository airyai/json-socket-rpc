# -*- encoding: utf-8 -*-
# $File: test01.py
# $Date: 2012-3-2 下午11:37:21
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
import client
import gevent, ssl

def do_test(clt):
    print (clt.call('echo', 'Hi'))
    print (clt.broadcast('echo', 'hello, world!'))

# following will raise SSLError if certificate not verified
clt = client.Client(('127.0.0.1', 9999),
                    ssl_version=ssl.PROTOCOL_SSLv23,
                    cert_reqs=ssl.CERT_REQUIRED,
                    ca_certs='certs/keys/ca.crt')
gevent.spawn(do_test, clt)
clt.serve()

