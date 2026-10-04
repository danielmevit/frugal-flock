# Frugal Flock — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('plan_store', Path(__file__).parents[1] / 'plan_store.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PlanStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='plan-store-')
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        (self.workspace / 'coord').mkdir()
        self.store = module.PlanStore(self.workspace)
        self.addCleanup(self.store.close)
        self.directory = self.workspace / 'coord/ui-plans'

    def test_restart_preserves_literal_request_and_revision_hash(self):
        request = 'Find café entries.\n$ this is text, not a command\n- ../../private'
        created = self.store.create(request)
        self.assertEqual(created['state'], 'draft')
        self.assertEqual(created['request'], request)
        self.assertEqual(len(created['content_sha256']), 64)
        self.store.close()
        with module.PlanStore(self.workspace) as restored:
            self.assertEqual(restored.get(created['id']), created)
        self.assertEqual({p.name for p in (self.workspace / 'coord').iterdir()}, {'ui-plans'})

    def test_invalid_requests_create_no_records(self):
        for value in ('', ' \n\t', 'x' * 4001, None, {}, 1):
            with self.subTest(value=str(value)[:20]):
                with self.assertRaises(ValueError):
                    self.store.create(value)
        self.assertEqual(list(self.directory.iterdir()), [])
        self.assertEqual(len(self.store.create('x' * 4000)['request']), 4000)

    def test_invalid_ids_cannot_select_paths(self):
        for value in ('../secret', '/tmp/secret', 'a' * 33, 'A' * 32, None, 'a' * 32 + '.json'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.store.get(value)

    def test_collision_never_overwrites_existing_record(self):
        fixed = type('FixedUUID', (), {'hex': 'a' * 32})()
        with patch.object(module.uuid, 'uuid4', return_value=fixed):
            original = self.store.create('Keep this draft')
            with self.assertRaises(FileExistsError):
                self.store.create('Do not overwrite')
        self.assertEqual(self.store.get(original['id']), original)
        self.assertEqual([p.name for p in self.directory.iterdir()], ['a' * 32 + '.json'])

    def test_corrupt_or_forged_approval_fails_closed(self):
        created = self.store.create('Small request')
        path = self.directory / (created['id'] + '.json')
        original = json.loads(path.read_text())
        for raw in ('broken', json.dumps({**original, 'state': 'approved'}),
                    json.dumps({**original, 'schema_version': True}),
                    json.dumps({**original, 'command': 'forbidden'}),
                    json.dumps({**original, 'created_at': '2026-10-04'}), 'x' * 65537):
            with self.subTest(raw=raw[:50]):
                path.write_text(raw)
                with self.assertRaises((ValueError, UnicodeError)):
                    self.store.get(created['id'])

    def test_symlink_and_fifo_records_are_refused(self):
        identity = 'b' * 32
        target = self.workspace / 'external.json'
        target.write_text('PRIVATE')
        path = self.directory / (identity + '.json')
        path.symlink_to(target)
        with self.assertRaises(OSError):
            self.store.get(identity)
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(ValueError):
            self.store.get(identity)
        self.assertEqual(target.read_text(), 'PRIVATE')

    def test_symlink_storage_directory_or_coordination_is_refused(self):
        self.store.close()
        self.directory.rmdir()
        target = self.workspace / 'outside'; target.mkdir()
        self.directory.symlink_to(target, target_is_directory=True)
        with self.assertRaises(OSError):
            module.PlanStore(self.workspace)
        self.directory.unlink()
        (self.workspace / 'coord').rmdir()
        (self.workspace / 'coord').symlink_to(target, target_is_directory=True)
        with self.assertRaises(OSError):
            module.PlanStore(self.workspace)
        self.assertEqual(list(target.iterdir()), [])

    def test_parallel_creates_publish_complete_unique_records(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as workers:
            drafts = list(workers.map(lambda i: self.store.create('Request ' + str(i)), range(20)))
        self.assertEqual(len({record['id'] for record in drafts}), 20)
        self.assertEqual(len(list(self.directory.iterdir())), 20)
        for draft in drafts:
            self.assertEqual(self.store.get(draft['id']), draft)


if __name__ == '__main__':
    unittest.main(verbosity=2)
