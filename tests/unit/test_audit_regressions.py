"""Provider-free regression checks against exact production function bodies."""
import ast
import base64
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def load_function(relative, name, namespace=None):
    tree = ast.parse((ROOT / relative).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    function.decorator_list = []
    code = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), function], type_ignores=[])
    ast.fix_missing_locations(code)
    scope = {} if namespace is None else namespace
    exec(compile(code, str(ROOT / relative), 'exec'), scope)
    return scope[name]


class AuditRegressions(unittest.TestCase):
    def test_zero_overlap_preserves_every_character(self):
        split = load_function('autogpt/commands/file_operations.py', 'split_file')
        for text in ('', 'a', 'abcd', 'abcde', 'abcdefgh', 'abcdefghijk'):
            for width in (1, 2, 4, 20):
                chunks = list(split(text, width, 0))
                self.assertEqual(''.join(chunks), text)
                self.assertTrue(all(0 < len(chunk) <= width for chunk in chunks))

    def test_overlap_and_invalid_bounds(self):
        split = load_function('autogpt/commands/file_operations.py', 'split_file')
        self.assertEqual(list(split('abcdefgh', 4, 1)), ['abcd', 'defg', 'gh'])
        for width, overlap in ((0, 0), (-1, 0), (4, -1), (4, 4), (4, 5)):
            with self.assertRaises(ValueError):
                list(split('abc', width, overlap))

    def test_dalle_size_is_forwarded_and_output_saved(self):
        calls = []
        def create(**kwargs):
            calls.append(kwargs)
            return {'data': [{'b64_json': base64.b64encode(b'fixture-image').decode()}]}
        with tempfile.TemporaryDirectory() as folder:
            function = load_function('autogpt/commands/image_gen.py', 'generate_image_with_dalle', {
                'openai': SimpleNamespace(Image=SimpleNamespace(create=create)),
                'CFG': SimpleNamespace(openai_api_key='dummy'),
                'b64decode': base64.b64decode,
                'path_in_workspace': lambda filename: Path(folder) / filename,
            })
            for size, expected in ((256, '256x256'), (512, '512x512'), (800, '1024x1024')):
                self.assertEqual(function('fixture', 'image.jpg', size), 'Saved to disk:image.jpg')
                self.assertEqual(calls[-1]['size'], expected)
                self.assertEqual((Path(folder) / 'image.jpg').read_bytes(), b'fixture-image')


if __name__ == '__main__':
    unittest.main()
