"""Offline AST extraction; never imports or executes upstream modules.

Run: python3 src/semdrift/extract_tools.py --source vendor/AssetOpsBench
Schemas are static reconstructions, not live MCP captures. Unknown annotations
are retained in x_source_annotation, never assigned an invented type.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

PIN = '0d044061ab3ffd4b213ddf6a0868c360d7e9667c'
SERVERS = ('iot', 'utilities', 'fmsr', 'wo')
WRITES = {'add_failure_modes', 'generate_work_order', 'update_workorder',
          'approve_workorder', 'assign_technician', 'close_workorder', 'cancel_workorder'}


def annotation(node):
    if isinstance(node, ast.Constant) and node.value is None:
        return {'type': 'null'}
    if isinstance(node, ast.Name):
        types = {'str': 'string', 'int': 'integer', 'float': 'number',
                 'bool': 'boolean', 'None': 'null', 'dict': 'object', 'list': 'array'}
        if node.id == 'Any':
            return {}
        if node.id in types:
            return {'type': types[node.id]}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return {'anyOf': [annotation(node.left), annotation(node.right)]}
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        name = node.value.id
        args = list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]
        if name == 'Optional':
            return {'anyOf': [annotation(args[0]), {'type': 'null'}]}
        if name == 'Union':
            return {'anyOf': [annotation(a) for a in args]}
        if name in ('List', 'list'):
            return {'type': 'array', 'items': annotation(args[0])}
        if name in ('Dict', 'dict') and ast.unparse(args[0]) == 'str':
            return {'type': 'object', 'additionalProperties': annotation(args[1])}
    return {'x_source_annotation': ast.unparse(node) if node else '<unannotated>'}


def nullable(schema):
    return schema.get('type') == 'null' or any(nullable(x) for x in schema.get('anyOf', []))


def literal(node, constants):
    if isinstance(node, ast.Name) and node.id in constants:
        return constants[node.id]
    return ast.literal_eval(node)  # Fail closed for dynamic expressions.


def schema(fn, constants):
    args = fn.args
    if args.vararg or args.kwarg or args.posonlyargs:
        raise ValueError(f'Unsupported signature: {fn.name}')
    defaults = [None] * (len(args.args) - len(args.defaults)) + args.defaults
    props, required = {}, []
    for arg, default in zip(args.args + args.kwonlyargs, defaults + args.kw_defaults):
        prop = annotation(arg.annotation)
        if default is not None:
            prop['default'] = literal(default, constants)
        elif not nullable(prop):
            required.append(arg.arg)
        props[arg.arg] = prop
    result = {'type': 'object', 'properties': props}
    if required:
        result['required'] = required
    return result


def extract(source):
    rows = []
    for server in SERVERS:
        tree = ast.parse((source / f'src/servers/{server}/main.py').read_text())
        funcs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assignments = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign)
                       for t in n.targets if isinstance(t, ast.Name)}
        constants = {}
        for key, value in assignments.items():
            try:
                constants[key] = ast.literal_eval(value)
            except (ValueError, TypeError):
                pass
        selected = []
        if server == 'wo':
            # Verify the default registration expression and central call before
            # interpreting these lists. Do not use backend functions with db/now.
            expected = "_READ_TOOLS if os.environ.get('AOB_READONLY') == '1' else _READ_TOOLS + _WRITE_TOOLS"
            if ast.unparse(assignments['_TOOLS']) != expected:
                raise ValueError('WO registration changed; review required')
            loops = [n for n in tree.body if isinstance(n, ast.For) and ast.unparse(n.iter) == '_TOOLS']
            if len(loops) != 1 or ast.unparse(loops[0].body[0]) != 'mcp.tool(title=_title, annotations=_TOOL_ANNOTATIONS.get(_fn))(_fn)':
                raise ValueError('WO registration call changed; review required')
            for group in ('_READ_TOOLS', '_WRITE_TOOLS'):
                for item in assignments[group].elts:
                    selected.append((funcs[item.elts[0].id], {}))
        else:
            for fn in funcs.values():
                for deco in fn.decorator_list:
                    if isinstance(deco, ast.Call) and ast.unparse(deco.func) == 'mcp.tool':
                        selected.append((fn, {k.arg: literal(k.value, constants) for k in deco.keywords
                                              if k.arg in ('name', 'description')}))
        for fn, options in selected:
            name = options.get('name', fn.name)
            desc = options.get('description', ast.get_docstring(fn, clean=True))
            if not desc:
                raise ValueError(f'No description: {name}')
            rows.append({'name': name, 'server': server, 'access': 'write' if name in WRITES else 'read',
                         'description': desc, 'input_schema': schema(fn, constants)})
    if len(rows) < 35:
        raise ValueError('Fewer than 35 tools; inspect optional servers before proceeding')
    if len({r['name'] for r in rows}) != len(rows):
        raise ValueError('Duplicate names')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('vendor/AssetOpsBench'))
    parser.add_argument('--output', type=Path, default=Path('datasets/tools/v0_original.json'))
    args = parser.parse_args()
    sha = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip()
    if sha != PIN:
        raise SystemExit(f'Expected {PIN}, got {sha}; review source version first')
    rows = extract(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n')
    print(f'Extracted {len(rows)} tools at {sha}; output SHA256 {hashlib.sha256(args.output.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
