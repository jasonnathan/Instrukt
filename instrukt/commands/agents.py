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
"""Agent commands"""

import asyncio
from rich.markdown import Markdown
from .root_cmd import ROOT as root
from ..commands.command import CmdGroup, CallbackOutput, CmdLog
from ..context import Context
from ..utils.debug import notify
import typing as t

from ..agent import (
        AgentLoader,
        ModuleManager,
        AgentEvents,
        AgentState,
        )

from instrukt.messages.agents import AgentLoaded
from instrukt.errors import AgentError



@root.group(name="agent")
class Agent(CmdGroup):
    """Agent related commands."""

    @staticmethod
    async def cmd_load(ctx: Context, name: str) -> CallbackOutput:
        """Load/activate an agent by `name`."""
        assert ctx.app is not None
        await ctx.app.agent_manager.load_agent(name)
        return CmdLog(f"Loading agent ... {name}")

    @staticmethod
    async def cmd_switch(ctx: Context, name: str) -> CallbackOutput:
        """Switch to an agent by `name`."""
        assert ctx.app is not None
        await ctx.app.agent_manager.switch_agent(name)
        return CmdLog(f"Switching agent ... {name}")

    @staticmethod
    async def cmd_stop(ctx: Context) -> CallbackOutput:
        """Stop the active agent."""
        if not await ctx.app.agent_manager.active_agent.stop_agent(ctx): # type: ignore
            return CmdLog("Agent is not running.")
        else:
            return CmdLog("Stopping agent ...")

    #HACK: unload agent and clear state and callbacks
    @staticmethod
    async def cmd_unload(ctx: Context) -> CallbackOutput:
        """Unloads the currently loaded agent."""
        assert ctx.app is not None
        ctx.app.active_agent.realm.stop_session()
        del ctx.app.active_agent
        return CmdLog("Unloaded agent.")

    @staticmethod
    async def cmd_list(ctx: Context) -> CallbackOutput:
        """Lists loadable agents."""
        agents = list(ModuleManager.list_modules())
        # print as a markdown list
        _agents = """\nAvailable Agents:\n"""
        for a in agents:
            _agents += (f"- {a}\n")
        _agents += "---"
        return Markdown(_agents)

    @staticmethod
    async def cmd_list_active(ctx: Context) -> CallbackOutput:
        """Lists active agents by `name`."""
        assert ctx.app is not None
        return(ctx.app.agent_manager.loaded_agents)

    # @staticmethod
    # async def cmd_add_tool(ctx: Context) -> CallbackOutput:
    #     """Add a tool to the active agent."""
    #     assert ctx.app is not None
    #     am = ctx.app.agent_manager
    #     await am.add_tool()

    @staticmethod
    async def cmd_update_tool_name(ctx: Context, old: str, new: str) -> None:
        """Update an attached tool name."""
        agent = ctx.app.agent_manager.active_agent
        if agent is not None:
            agent.update_tool_name(old, new)


    @staticmethod
    async def cmd_list_tools(ctx: Context) -> list[str]:
        """Lists attached tools."""
        return ctx.app.agent_manager.active_agent.attached_tools

    @staticmethod
    async def cmd_clear_memory(ctx: Context) -> CallbackOutput:
        """Clears the agent's memory."""
        ctx.app.agent_manager.active_agent.memory.clear()
        ctx.app.agent_manager.active_agent.reload_agent()
        return CmdLog("Cleared agent's memory.")

    async def cmd_forget(ctx: Context, term: str) -> CallbackOutput:
        """Forgets a term in the agent's memory."""
        ctx.app.agent_manager.active_agent.forget_about(term)
        ctx.app.agent_manager.active_agent.reload_agent()
        return CmdLog(f"Forgot {term}.")





