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
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Sequence,
    Union,
    cast
)

from langchain.vectorstores import Chroma as ChromaVectorStore
from langchain.embeddings import HuggingFaceEmbeddings


from ..config import CHROMA_INSTALLED
from ..utils.asynctools import run_async
from .schema import Collection
from .retrieval import retrieval_tool_from_index

if TYPE_CHECKING:
    import chromadb   # type: ignore
    from langchain.embeddings.base import Embeddings
    from ..tools.base import SomeTool

log = logging.getLogger(__name__)

TEmbeddings = Union["Embeddings", "HuggingFaceEmbeddings"]


DEFAULT_EMBEDDINGS_MODEL = "sentence-transformers/all-mpnet-base-v2"
DEFAULT_COLLECTION_NAME = "instrukt"


class ChromaWrapper(ChromaVectorStore):
    """Wrapper around Chroma DB."""

    def __init__(
            self,
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

        #TODO!: use the stored embedding_fn name to spawn the embedding_fn
        if embedding_function is None:
            embedding_function = HuggingFaceEmbeddings(
                model_name=DEFAULT_EMBEDDINGS_MODEL)

        embedding_fn = f"{type(embedding_function).__module__}\
                .{type(embedding_function).__name__}"

        log.debug(f"Using embedding function {embedding_fn}")

        collection_metadata = collection_metadata or {}
        collection_metadata["embedding_fn"] = embedding_fn

        if type(embedding_function) is HuggingFaceEmbeddings:
            collection_metadata["model_name"] = embedding_function.model_name
        log.debug(collection_metadata)


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
