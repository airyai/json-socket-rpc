# -*- encoding: utf-8 -*-
# $File: pastebin.py
# $Date: 2012-3-1 下午7:40:02
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
import server

logging.basicConfig(level=logging.DEBUG, 
            format='[%(asctime)s %(module)s.py:%(lineno)s] %(message)s',
            datefmt='%H:%M:%S')
logging.debug('Server started.')

svr = server.Server(('127.0.0.1', 9999))
svr.serve_forever()

