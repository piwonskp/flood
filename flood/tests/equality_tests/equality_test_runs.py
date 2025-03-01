from __future__ import annotations

import typing

import flood
from . import equality_test_sets
from .input_generator import get_block_range_and_tx


def run_equality_test(
    test_name: str,
    nodes: flood.NodesShorthand,
    *,
    verbose: bool | int = True,
    random_seed: flood.RandomSeed | None = None,
    output_dir: str | None = None,
) -> None:
    import json
    import os
    import requests
    import toolstr

    nodes = flood.parse_nodes(nodes, request_metadata=True)
    for node in nodes.values():
        if node['remote'] is not None:
            raise Exception('remote not supported for equality test')
    if len(nodes) != 2:
        raise Exception('should use two nodes in equality test')

    equality_tests = equality_test_sets.get_all_equality_tests(*get_block_range_and_tx(nodes))

    # get tests
    if test_name != 'all':
        equality_tests = [t for t in equality_tests if t[0] == test_name]
        if not equality_tests:
            raise NotImplementedError(
                'no matching test found for name "' + test_name + '"'
            )

    if output_dir is None:
        import tempfile

        output_dir = tempfile.mkdtemp()

    # print preamble
    flood.print_text_box('Equality test: ' + test_name)
    flood.print_bullet(key='methods', value='')
    for test in equality_tests:
        flood.print_bullet(key=test[0], value='', colon_str='', indent=4)
    flood.print_bullet(key='output_dir', value=output_dir)
    flood.print_bullet(key='nodes', value='')
    for n, node in enumerate(nodes.values()):
        toolstr.print(
            toolstr.add_style(str(n + 1), flood.styles['metavar'])
            + '. '
            + str(node),
            indent=4,
            style=flood.styles['description'],
        )

    # run test
    successful = []
    calls = {}
    call_node_responses: typing.Any = {}
    headers = {'Content-Type': 'application/json', 'User-Agent': 'flood'}
    for test in equality_tests:
        # create call
        test_name, constructor, args, kwargs = test
        call = constructor(*args, **kwargs)
        calls[test_name] = call
        call_node_responses.setdefault(test_name, {})

        # dispatch call
        results = []
        responses = []
        for node in nodes.values():
            response = None
            try:
                response = requests.post(
                    url=node['url'], data=json.dumps(call), headers=headers
                )
                response_data = response.json()
                if 'result' in response_data:
                    result = response_data['result']
                else:
                    result = None
            except Exception:
                result = None
            responses.append(response)
            results.append(result)
            call_node_responses[test_name][node['name']] = result

        # print summary
        success = _summarize_result(
            responses=responses,
            results=results,
            nodes=nodes,
            test=test,
            call=call,
        )
        if success:
            successful.append(test_name)
    failed = [test[0] for test in equality_tests if test[0] not in successful]

    # save output file
    summary = {
        'calls': calls,
        'successful': successful,
        'failed': failed,
        'responses': call_node_responses,
    }
    file_path = os.path.join(output_dir, 'equality_results.json')
    with open(file_path, 'w') as f:
        json.dump(summary, f)

    # summarize test
    print()
    flood.print_text_box('Equality Test Summary')
    print()
    flood.print_header(
        'No differences detected (n = ' + str(len(successful)) + ')'
    )
    if len(successful) == 0:
        print('[none]')
    else:
        for name in sorted(successful):
            flood.print_bullet(key=name, value='', colon_str='')
    print()
    flood.print_header('Differences detected (n = ' + str(len(failed)) + ')')
    if len(failed) == 0:
        print('[none]')
    else:
        for name in sorted(failed):
            flood.print_bullet(key=name, value='', colon_str='')
    print()
    toolstr.print(
        'summary saved to: ' + file_path, style=flood.styles['comment']
    )


def _summarize_result(
    responses: typing.Sequence[typing.Any],
    results: typing.Sequence[typing.Any],
    nodes: flood.Nodes,
    test: flood.EqualityTest,
    call: typing.Mapping[str, typing.Any],
) -> bool:
    import toolstr

    test_name, constructor, args, kwargs = test

    if results[0] is None or not toolstr.nested_equal(results[0], results[1]):
        print()
        flood.print_text_box('Discrepancies in ' + test_name)
        print()
        flood.print_header('args')
        if len(args) > 0:
            for arg in args:
                flood.print_bullet(key=arg, value='', colon_str='')
        if len(kwargs) > 0:
            for key, value in kwargs.items():
                flood.print_bullet(key=key, value=value)
        print()
        flood.print_header('call')
        print(call)

        if any(result is None for result in results):
            print()
        for node, result, response in zip(nodes.values(), results, responses):
            if result is None:
                toolstr.print(
                    node['name'] + ' failed', style=flood.styles['title']
                )
                if response is None:
                    print('response: no response')
                elif response.status_code == 200:
                    print('response:', response.json())
                else:
                    print('response: status code ', response.status_code)

        if results[0] is None or results[1] is None:
            return False

        if len(results) == 2:
            node0, node1 = list(nodes.values())
            print()
            flood.print_header('differences in response')
            toolstr.print_nested_diff(
                lhs=results[0],
                rhs=results[1],
                lhs_name=node0['name'],
                rhs_name=node1['name'],
                styles=flood.styles,
                indent=4,
            )
        else:
            print('omitting details when >2 nodes tested')

        return False

    else:
        return True

