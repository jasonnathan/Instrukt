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
"""Chroma wrapper and utils."""

import logging
from typing import (
                    cast,
                    TYPE_CHECKING,
                    Any,
                    Dict,
                    Optional,
                    Sequence,
                    Union
                )


import chromadb
from langchain.embeddings import ( HuggingFaceEmbeddings,
                                    HuggingFaceInstructEmbeddings
                                )
from langchain.vectorstores import Chroma as ChromaVectorStore

from ..config import CHROMA_INSTALLED
from ..utils.asynctools import run_async
from .retrieval import retrieval_tool_from_index
from .schema import Collection

if TYPE_CHECKING:
    import chromadb  # type: ignore
    from langchain.embeddings.base import Embeddings

    from ..tools.base import SomeTool

log = logging.getLogger(__name__)

TEmbeddings = Union["Embeddings", "HuggingFaceEmbeddings",
                    "HuggingFaceInstructEmbeddings"]

DEFAULT_EMBEDDINGS_MODEL = "sentence-transformers/all-mpnet-base-v2"


class ChromaWrapper(ChromaVectorStore):
    """Wrapper around Chroma DB."""

    def __init__(self,
                 client: "chromadb.Client",
                 collection_name: str,
                 embedding_function: Optional[TEmbeddings] = None,
                 collection_metadata: Optional[Dict[str, Any]] = None,
                 **kwargs):
        if not CHROMA_INSTALLED:
            raise ImportError(
                "Instrukt tried to import chromadb, but it is not installed."
                " chromadb is required for using instrukt knowledge features."
                " Please install it with `pip install instrukt[chromadb]`")

        collection_metadata = collection_metadata or {}

        if embedding_function is None:
            embedding_function = HuggingFaceEmbeddings(
                model_name=DEFAULT_EMBEDDINGS_MODEL)

        #HACK: embedding_fn details are always saved again in the collection metadata
        #TODO!: should only stored when index is created
        embedding_fn_fqn = f"{type(embedding_function).__module__}.{type(embedding_function).__name__}"

        collection_metadata["embedding_fn"] = embedding_fn_fqn

        if type(embedding_function) in (HuggingFaceEmbeddings, HuggingFaceInstructEmbeddings):
            collection_metadata["model_name"] = cast(
                "HuggingFaceEmbeddings", embedding_function).model_name

        _kwargs = {
            **kwargs,
            **{
                "client": client,
                "collection_name": collection_name,
                "embedding_function": embedding_function,
                "collection_metadata": collection_metadata,
            }
        }
        super().__init__(**_kwargs)

    async def adelete(self,
                      ids: list[str] | None = None,
                      where: dict[Any, Any] | None = None):
        await run_async(self._collection.delete, ids=ids, where=where)

    async def adelete_collection(self):
        await run_async(self._client.delete_collection, self._collection.name)

    async def adelete_named_collection(self, collection_name: str):
        await run_async(self._client.delete_collection, collection_name)

    #TODO: async document adding

    async def acount(self) -> int:
        return await run_async(self._collection.count)

    def count(self) -> int:
        return self._collection.count()

    def list_collections(self) -> Sequence[Collection]:
        """Bypass default chroma listing method that does not rely on
        embeddings function."""

        return self._client.list_collections()

    @property
    def metadata(self) -> dict[Any, Any] | None:
        """Returns the collection metadata."""
        return self._collection.metadata

    @property
    def description(self) -> str | None:
        """Return the collection's description if it exists."""
        # metadata has to be not None and be a dict with the key description
        if self.metadata is not None and "description" in self.metadata:
            return self.metadata["description"]
        return None

    def get_retrieval_tool(self,
                           description: str | None = None,
                           return_direct: bool = False,
                           **kwargs) -> "SomeTool":
        """Get a retrieval tool for this collection."""
        return retrieval_tool_from_index(self,
                                         description,
                                         return_direct=return_direct,
                                         **kwargs)
