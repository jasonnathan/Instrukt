## 
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
## 
##  SPDX-License-Identifier: AGPL-3.0-or-later
## 
##  This file is part of Instrukt.
## 
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
## 
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
## 
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
## 
from typing import TYPE_CHECKING, Any, Union, cast

from textual.message import Message
from textual.dom import DOMNode

if TYPE_CHECKING:
    from .messages.agents import AgentMessage
    from .messages.log import LogMessage
    from .app import InstruktApp

    AnyMessage = Union[
        Message,
        AgentMessage,
        LogMessage,
    ]

AnyDict = dict[Any, Any]

class InstruktDomNodeMixin(DOMNode):
    @property
    def _app(self) -> "InstruktApp":
        return cast("InstruktApp", self.app)
