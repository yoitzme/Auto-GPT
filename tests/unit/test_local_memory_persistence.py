"""Load the real memory module with only the external embedding provider isolated."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np
import orjson


class LocalMemoryPersistence(unittest.TestCase):
    def load_cache(self, embed):
        provider = ModuleType('autogpt.llm_utils')
        provider.create_embedding_with_ada = embed
        base = ModuleType('autogpt.memory.base')
        base.MemoryProviderSingleton = object
        path = Path(__file__).resolve().parents[2] / 'autogpt/memory/local.py'
        spec = importlib.util.spec_from_file_location('memory_under_review', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'autogpt.llm_utils': provider,
                                     'autogpt.memory.base': base,
                                     'memory_under_review': module}):
            spec.loader.exec_module(module)
        return module

    def test_restart_preserves_bytes_and_restores_searchable_vectors(self):
        module = self.load_cache(lambda _: [1.0] + [0.0] * 1535)
        with tempfile.TemporaryDirectory() as directory:
            index = str(Path(directory) / 'memory')
            file = Path(index + '.json')
            original = orjson.dumps({'texts': ['remember me'],
                                    'embeddings': [[1.0] + [0.0] * 1535]})
            file.write_bytes(original)
            cache = module.LocalCache(SimpleNamespace(memory_index=index))
            self.assertEqual(file.read_bytes(), original)
            self.assertEqual(cache.get_stats(), (1, (1, 1536)))
            self.assertEqual(cache.get_relevant('query', 1), ['remember me'])
            cache.add('second')
            restored = module.LocalCache(SimpleNamespace(memory_index=index))
            self.assertEqual(restored.data.texts, ['remember me', 'second'])

    def test_failed_embedding_does_not_append_unpaired_text(self):
        def fail(_):
            raise RuntimeError('provider unavailable')
        module = self.load_cache(fail)
        with tempfile.TemporaryDirectory() as directory:
            index = str(Path(directory) / 'memory')
            cache = module.LocalCache(SimpleNamespace(memory_index=index))
            with self.assertRaises(RuntimeError):
                cache.add('must not be added')
            self.assertEqual(cache.get_stats(), (0, (0, 1536)))
            self.assertFalse(Path(index + '.json').exists())

    def test_cleared_memory_does_not_return_after_restart(self):
        module = self.load_cache(lambda _: [1.0] + [0.0] * 1535)
        with tempfile.TemporaryDirectory() as directory:
            index = str(Path(directory) / 'memory')
            cache = module.LocalCache(SimpleNamespace(memory_index=index))
            cache.add('must be forgotten')
            cache.clear()
            restored = module.LocalCache(SimpleNamespace(memory_index=index))
            self.assertEqual(restored.get_stats(), (0, (0, 1536)))

    def test_failed_replace_preserves_last_durable_memory_and_in_memory_pairing(self):
        module = self.load_cache(lambda _: [1.0] + [0.0] * 1535)
        with tempfile.TemporaryDirectory() as directory:
            index = str(Path(directory) / 'memory')
            cache = module.LocalCache(SimpleNamespace(memory_index=index))
            cache.add('durable')
            original = Path(index + '.json').read_bytes()
            with patch.object(module.os, 'replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    cache.add('not durable')
            self.assertEqual(Path(index + '.json').read_bytes(), original)
            self.assertEqual(cache.get_stats(), (1, (1, 1536)))
            self.assertEqual(list(Path(directory).iterdir()), [Path(index + '.json')])


if __name__ == '__main__':
    unittest.main()
