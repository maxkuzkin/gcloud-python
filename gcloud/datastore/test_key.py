# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest2


class TestKey(unittest2.TestCase):

    def _getTargetClass(self):
        from gcloud.datastore.key import Key
        return Key

    def _makeOne(self, *args, **kwargs):
        return self._getTargetClass()(*args, **kwargs)

    def test_ctor_empty(self):
        self.assertRaises(ValueError, self._makeOne)

    def test_ctor_explicit(self):
        _DATASET = 'DATASET'
        _NAMESPACE = 'NAMESPACE'
        _KIND = 'KIND'
        _ID = 1234
        _PATH = [{'kind': _KIND, 'id': _ID}]
        key = self._makeOne(_KIND, _ID, namespace=_NAMESPACE,
                            dataset_id=_DATASET)
        self.assertEqual(key.dataset_id, _DATASET)
        self.assertEqual(key.namespace, _NAMESPACE)
        self.assertEqual(key.kind, _KIND)
        self.assertEqual(key.path, _PATH)

    def test_ctor_bad_kind(self):
        self.assertRaises(ValueError, self._makeOne, object())

    def test_ctor_bad_id_or_name(self):
        self.assertRaises(ValueError, self._makeOne, 'KIND', object())
        self.assertRaises(ValueError, self._makeOne, 'KIND', None)
        self.assertRaises(ValueError, self._makeOne, 'KIND', 10, 'KIND2', None)

    def test__clone(self):
        _DATASET = 'DATASET'
        _NAMESPACE = 'NAMESPACE'
        _KIND = 'KIND'
        _ID = 1234
        _PATH = [{'kind': _KIND, 'id': _ID}]
        key = self._makeOne(_KIND, _ID, namespace=_NAMESPACE,
                            dataset_id=_DATASET)
        clone = key._clone()
        self.assertEqual(clone.dataset_id, _DATASET)
        self.assertEqual(clone.namespace, _NAMESPACE)
        self.assertEqual(clone.kind, _KIND)
        self.assertEqual(clone.path, _PATH)

    def test_to_protobuf_defaults(self):
        from gcloud.datastore.datastore_v1_pb2 import Key as KeyPB
        _KIND = 'KIND'
        key = self._makeOne(_KIND)
        pb = key.to_protobuf()
        self.assertTrue(isinstance(pb, KeyPB))

        # Check partition ID.
        self.assertEqual(pb.partition_id.dataset_id, '')
        self.assertFalse(pb.partition_id.HasField('dataset_id'))
        self.assertEqual(pb.partition_id.namespace, '')
        self.assertFalse(pb.partition_id.HasField('namespace'))

        # Check the element PB matches the partial key and kind.
        elem, = list(pb.path_element)
        self.assertEqual(elem.kind, _KIND)
        self.assertEqual(elem.name, '')
        self.assertFalse(elem.HasField('name'))
        self.assertEqual(elem.id, 0)
        self.assertFalse(elem.HasField('id'))

    def test_to_protobuf_w_explicit_dataset(self):
        _DATASET = 'DATASET'
        key = self._makeOne('KIND', dataset_id=_DATASET)
        pb = key.to_protobuf()
        self.assertEqual(pb.partition_id.dataset_id, _DATASET)

    def test_to_protobuf_w_explicit_namespace(self):
        _NAMESPACE = 'NAMESPACE'
        key = self._makeOne('KIND', namespace=_NAMESPACE)
        pb = key.to_protobuf()
        self.assertEqual(pb.partition_id.namespace, _NAMESPACE)

    def test_to_protobuf_w_explicit_path(self):
        _PARENT = 'PARENT'
        _CHILD = 'CHILD'
        _ID = 1234
        _NAME = 'NAME'
        key = self._makeOne(_PARENT, _NAME, _CHILD, _ID)
        pb = key.to_protobuf()
        elems = list(pb.path_element)
        self.assertEqual(len(elems), 2)
        self.assertEqual(elems[0].kind, _PARENT)
        self.assertEqual(elems[0].name, _NAME)
        self.assertEqual(elems[1].kind, _CHILD)
        self.assertEqual(elems[1].id, _ID)

    def test_to_protobuf_w_no_kind(self):
        key = self._makeOne('KIND')
        # Force the 'kind' to be unset. Maybe `to_protobuf` should fail
        # on this? The backend certainly will.
        key._path[-1].pop('kind')
        pb = key.to_protobuf()
        self.assertEqual(pb.partition_id.dataset_id, '')
        self.assertFalse(pb.path_element[0].HasField('kind'))

    def test_is_partial_no_name_or_id(self):
        key = self._makeOne('KIND')
        self.assertTrue(key.is_partial)

    def test_is_partial_w_id(self):
        _ID = 1234
        key = self._makeOne('KIND', _ID)
        self.assertFalse(key.is_partial)

    def test_is_partial_w_name(self):
        _NAME = 'NAME'
        key = self._makeOne('KIND', _NAME)
        self.assertFalse(key.is_partial)

    def test_id_or_name_no_name_or_id(self):
        key = self._makeOne('KIND')
        self.assertEqual(key.id_or_name, None)

    def test_id_or_name_no_name_or_id_child(self):
        key = self._makeOne('KIND1', 1234, 'KIND2')
        self.assertEqual(key.id_or_name, None)

    def test_id_or_name_w_id_only(self):
        _ID = 1234
        key = self._makeOne('KIND', _ID)
        self.assertEqual(key.id_or_name, _ID)

    def test_id_or_name_w_name_only(self):
        _NAME = 'NAME'
        key = self._makeOne('KIND', _NAME)
        self.assertEqual(key.id_or_name, _NAME)

    def test_parent_default(self):
        key = self._makeOne('KIND')
        self.assertEqual(key.parent, None)

    def test_parent_explicit_top_level(self):
        key = self._makeOne('KIND', 1234)
        self.assertEqual(key.parent, None)

    def test_parent_explicit_nested(self):
        _PARENT_KIND = 'KIND1'
        _PARENT_ID = 1234
        _PARENT_PATH = [{'kind': _PARENT_KIND, 'id': _PARENT_ID}]
        key = self._makeOne(_PARENT_KIND, _PARENT_ID, 'KIND2')
        self.assertEqual(key.parent.path, _PARENT_PATH)

    def test_parent_multiple_calls(self):
        _PARENT_KIND = 'KIND1'
        _PARENT_ID = 1234
        _PARENT_PATH = [{'kind': _PARENT_KIND, 'id': _PARENT_ID}]
        key = self._makeOne(_PARENT_KIND, _PARENT_ID, 'KIND2')
        parent = key.parent
        self.assertEqual(parent.path, _PARENT_PATH)
        new_parent = key.parent
        self.assertTrue(parent is new_parent)