#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import typing
import uuid
from typing import Iterable

from arch.api.base.data_table import Table
from arch.api import  WorkMode, Backend, RuntimeInstance
from arch.api.base.utils.store_type import StoreTypes
from arch.api.utils.profile_util import log_elapsed


def get_session(session_id, mode, backend, persistent_engine):
    from arch.api.impl.based_2x import build
    if RuntimeInstance.SESSION:
        return RuntimeInstance.SESSION
    if isinstance(mode, int):
        mode = WorkMode(mode)
    if isinstance(backend, int):
        backend = Backend(backend)
    if session_id is None:
        session_id = str(uuid.uuid1())

    builder = build.Builder(session_id=session_id, work_mode=mode, persistent_engine=persistent_engine)
    RuntimeInstance.MODE = mode
    RuntimeInstance.BACKEND = backend
    RuntimeInstance.BUILDER = builder
    RuntimeInstance.SESSION = builder.build_session()
    return RuntimeInstance.SESSION


def get_eggroll_table(_session, namespace, name, partition, **kwargs):
    table = _session.table(namespace=namespace, name=name, partition=partition, **kwargs)
    return table


# noinspection SpellCheckingInspection,PyProtectedMember,PyPep8Naming
class EggRollTable(Table):
    def __init__(self,
                 session_id,
                 mode: typing.Union[int, WorkMode] = WorkMode.STANDALONE,
                 backend: typing.Union[int, Backend] = Backend.EGGROLL,
                 persistent_engine: str = StoreTypes.ROLLPAIR_LMDB,
                 namespace: str = None,
                 name: str = None,
                 partition: int = 1,
                 **kwargs):
        self._name = name or str(uuid.uuid1())
        self._namespace = namespace or str(uuid.uuid1())
        self._partitions = partition
        self._session_id = session_id
        self._strage_engine = persistent_engine
        self.schema = {}
        self._session = get_session(session_id, mode, backend, persistent_engine)
        self._table = get_eggroll_table(_sdesson=self._session,
                                        namespace=namespace,
                                        name=name,
                                        partition=partition,
                                        **kwargs)

    def get_name(self):
        return self._name

    def get_namespace(self):
        return self._namespace

    def get_partitions(self):
        return self._table.get_partitions()

    def get_storage_engine(self):
        return self._strage_engine

    def get_address(self):
        return {'name': self._name, 'namespace': self._namespace}

    def put_all(self, kv_list: Iterable, use_serialize=True, chunk_size=100000):
        return self._table.put_all(kv_list, use_serialize, chunk_size)

    @log_elapsed
    def collect(self, min_chunk_size=0, use_serialize=True, **kwargs) -> list:
        return self._table.get_all(min_chunk_size, use_serialize, **kwargs)

    def delete(self, k, use_serialize=True):
        return self._table.delete(k=k, use_serialize=use_serialize)

    def destroy(self):
        return self._table.destroy()

    @classmethod
    def dtable(cls, session_id, name, namespace, partition):
        return EggRollTable(session_id=session_id, name=name, namespace=namespace, partition=partition)

    @log_elapsed
    def save_as(self, name, namespace, partition=None, use_serialize=True, **kwargs):

        from arch.api import RuntimeInstance
        options = kwargs.get("options", {})
        store_type = options.get("store_type", RuntimeInstance.SESSION.get_persistent_engine())
        options["store_type"] = store_type

        if partition is None:
            partition = self._partitions
        self._table.save_as(name=name, namespace=namespace, partition=partition, options=options)

        return self.dtable(self._session_id, name, namespace, partition)

    @log_elapsed
    def count(self, **kwargs):
        return self._table.count()




