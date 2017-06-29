from __future__ import print_function
import yaml
import inspect
import unittest
from dis import dis
from types import GeneratorType
from tornado.gen import coroutine, Task
from orderedattrdict import AttrDict
from orderedattrdict.yamlutils import AttrDictYAMLLoader
from gramex.transforms import build_transform, flattener, badgerfish, template


def yaml_parse(text):
    return yaml.load(text, Loader=AttrDictYAMLLoader)


@coroutine
def gen_str(val):
    'Sample coroutine method'
    yield Task(str, val)


class BuildTransform(unittest.TestCase):
    '''Test build_transform CODE output'''

    def eqfn(self, a, b):
        a_code, b_code = a.__code__, b.__code__

        # msg = parent function's name
        msg = inspect.stack()[1][3]

        src, tgt = a_code.co_code, b_code.co_code
        if src != tgt:
            # Print the disassembled code to make debugging easier
            print('Compiled by build_transform from YAML')      # noqa
            dis(src)
            print('Tested against test case')                   # noqa
            dis(tgt)
        self.assertEqual(src, tgt, '%s: code mismatch' % msg)

        src, tgt = a_code.co_argcount, b_code.co_argcount
        self.assertEqual(src, tgt, '%s: argcount %d != %d' % (msg, src, tgt))
        src, tgt = a_code.co_nlocals, b_code.co_nlocals
        self.assertEqual(src, tgt, '%s: nlocals %d != %d' % (msg, src, tgt))

    def check_transform(self, transform, yaml_code, vars=None):
        fn = build_transform(yaml_parse(yaml_code), vars=vars)
        self.eqfn(fn, transform)

    def test_no_function_raises_error(self):
        with self.assertRaises(KeyError):
            build_transform({})

    def test_fn(self):
        def transform(_val):
            result = len(_val)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: len
        ''')

    def test_fn_no_args(self):
        def transform():
            result = max(1, 2)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: max
            args: [1, 2]
        ''', vars={})

    def test_fn_args(self):
        def transform(_val):
            result = max(1, 2)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: max
            args: [1, 2]
        ''')

        def transform(_val):
            result = len('abc')
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: len
            args: abc
        ''')

        def transform(_val):
            result = range(10)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: range
            args: 10
        ''')

    def test_fn_args_var(self):
        def transform(x=1, y=2):
            result = max(x, y, 3)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: max
            args:
                - =x
                - =y
                - 3
        ''', vars=AttrDict([('x', 1), ('y', 2)]))

    def test_fn_kwargs(self):
        def transform(_val):
            result = dict(_val, a=1, b=2)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: dict
            kwargs: {a: 1, b: 2}
        ''')

    def test_fn_kwargs_complex(self):
        def transform(_val):
            result = dict(_val, a=[1, 2], b=AttrDict([('b1', 'x'), ('b2', 'y')]))
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: dict
            kwargs:
                a: [1, 2]
                b:
                    b1: x
                    b2: y
        ''')

    def test_fn_kwargs_var(self):
        def transform(x=1, y=2):
            result = dict(x, y, a=x, b=y, c=3, d='=4')
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: dict
            kwargs: {a: =x, b: =y, c: 3, d: ==4}
        ''', vars=AttrDict([('x', 1), ('y', 2)]))

    def test_fn_args_kwargs(self):
        def transform(_val):
            result = format(1, 2, a=3, b=4, c=5, d='=6')
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: format
            args: [1, 2]
            kwargs: {a: 3, b: 4, c: 5, d: ==6}
        ''')

    def test_fn_args_kwargs_var(self):
        def transform(x=1, y=2):
            result = format(x, y, a=x, b=y, c=3)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: format
            args: [=x, =y]
            kwargs: {a: =x, b: =y, c: =3}
        ''', vars=AttrDict([('x', 1), ('y', 2)]))

    def test_coroutine(self):
        def transform(_val):
            result = gen_str(_val)
            return result if isinstance(result, GeneratorType) else [result, ]
        self.check_transform(transform, '''
            function: testlib.test_transforms.gen_str
        ''')


class Badgerfish(unittest.TestCase):
    'Test gramex.transforms.badgerfish'

    def test_transform(self):
        result = yield badgerfish('''
        html:
          "@lang": en
          p: text
          div:
            p: text
        ''')
        self.assertEqual(
            result,
            '<!DOCTYPE html>\n<html lang="en"><p>text</p><div><p>text</p></div></html>')

    def test_mapping(self):
        result = yield badgerfish('''
        html:
          json:
            x: 1
            y: 2
        ''', mapping={
            'json': {
                'function': 'json.dumps',
                'kwargs': {'separators': [',', ':']},
            }
        })
        self.assertEqual(
            result,
            '<!DOCTYPE html>\n<html><json>{"x":1,"y":2}</json></html>')


class Template(unittest.TestCase):
    'Test gramex.transforms.template'
    def check(self, content, expected, **kwargs):
        result = yield template(content, **kwargs)
        self.assertEqual(result, expected)

    def test_template(self):
        self.check('{{ 1 }}', '1')
        self.check('{{ 1 + 2 }}', '3')
        self.check('{{ x + y }}', '3', x=1, y=2)


class Flattener(unittest.TestCase):
    def test_dict(self):
        fieldmap = {
            'all1': '',
            'all2': True,
            'x': 'x',
            'y.z': 'y.z',
            'z.1': 'z.1',
        }
        flat = flattener(fieldmap)
        src = {'x': 'X', 'y': {'z': 'Y.Z'}, 'z': ['Z.0', 'Z.1']}
        out = flat(src)
        self.assertEqual(out.keys(), fieldmap.keys())
        self.assertEqual(out['all1'], src)
        self.assertEqual(out['all2'], src)
        self.assertEqual(out['x'], src['x'])
        self.assertEqual(out['y.z'], src['y']['z'])
        self.assertEqual(out['z.1'], src['z'][1])

    def test_list(self):
        # Integer values must be interpreted as array indices
        fieldmap = {
            '0': 0,
            '1': '1',
            '2.0': '2.0',
        }
        flat = flattener(fieldmap)
        src = [0, 1, [2]]
        out = flat(src)
        self.assertEqual(out.keys(), fieldmap.keys())
        self.assertEqual(out['0'], src[0])
        self.assertEqual(out['1'], src[1])
        self.assertEqual(out['2.0'], src[2][0])

    def test_invalid(self):
        # None of these fields are valid. Don't raise an error, just ignore
        fieldmap = {
            0: 'int-invalid',
            ('a', 'b'): 'tuple-invalid',
            'false-invalid': False,
            'none-invalid': None,
            'float-invalid': 1.0,
            'dict-invalid': {},
            'tuple-invalid': tuple(),
            'set-invalid': set(),
            'list-invalid': [],
        }
        out = flattener(fieldmap)({})
        self.assertEqual(len(out.keys()), 0)
        fieldmap = {
            0.0: 'float-invalid',
        }
        out = flattener(fieldmap)({})
        self.assertEqual(len(out.keys()), 0)

    def test_default(self):
        fieldmap = {'x': 'x', 'y.a': 'y.a', 'y.1': 'y.1', 'z.a': 'z.a', '1': 1}
        default = 1
        flat = flattener(fieldmap, default=default)
        out = flat({'z': {}, 'y': []})
        self.assertEqual(out, {key: default for key in fieldmap})