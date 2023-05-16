"""

TODO
--methods parameter to specify methods
"""
from __future__ import annotations

import typing

import toolcli

import rpc_bench

help_message = """Load test JSON RPC endpoints

[bold][title]Test Specification[/bold][/title]
- [metavar]TEST[/metavar] can be a template, use [metavar]rpc_bench ls[/metavar] to list test templates
- Alternatively, [metavar]TEST[/metavar] can be a directory path of a previous test
    - This will rerun this the previous test, possibly on new nodes

[bold][title]Node Specification[/bold][/title]
- Nodes are specified as a space-separated list
- Basic node syntax is [metavar]url[/metavar] or [metavar]name=url[/metavar]
- The [metavar]name[/metavar] of each node is used for benchmark summary report

[bold][title]Remote Usage[/bold][/title]
- [metavar]rpc_bench[/metavar] can be invoked on remote machines
- Use node syntax [metavar]user@remote:node_url[/metavar] or [metavar]name=user@remote:node_url[/metavar]
- Can omit the [metavar]user@[/metavar] prefix if ssh config has username specified
- [metavar]rpc_bench[/metavar] must already be installed on each remote machine

[bold][title]Parameter Randomization[/bold][/title]
- [metavar]rpc_bench[/metavar] can call each RPC method multiple times using [metavar]-n <N>[/metavar]
- For each call, parameters are randomized to minimize caching effects
- Specify random seed [metavar]-s <seed>[/metavar] for repeatable set of randomized calls"""


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': root_command,
        'help': help_message,
        'args': [
            {
                'name': 'test',
                'help': 'test to run (use [metavar]rpc_bench ls[/metavar] for list)',
            },
            {
                'name': 'nodes',
                'nargs': '+',
                'help': 'nodes to test, see syntax above',
            },
            {
                'name': ['-s', '--seed'],
                'dest': 'random_seed',
                'type': int,
                'help': 'random seed to use, default is current timestamp',
            },
            {
                'name': ['-q', '--quiet'],
                'help': 'do not print output to [metavar]STDOUT[/metavar]',
                'action': 'store_true',
            },
            {
                'name': ['-m', '--mode'],
                'choices': ['stress', 'spike', 'soak'],
                'help': 'stress, spike, soak, latency, or equality',
            },
            {
                'name': ['--metrics'],
                'nargs': '+',
                'help': 'space-separated list of performance metrics to show',
            },
            {
                'name': ['-r', '--rates'],
                'nargs': '+',
                'help': 'rates to use in load test (requests per second)',
            },
            {
                'name': ['-d', '--duration'],
                'type': int,
                'help': 'amount of time to test each rate',
            },
            {
                'name': ['--dry'],
                'help': 'only construct tests, do not run them',
                'action': 'store_true',
            },
            {
                'name': ['-o', '--output'],
                'help': 'directory to save results, default is tmp dir',
            },
        ],
        'examples': [
            'eth_getBlockByNumber localhost:8545',
            'eth_getLogs localhost:8545 localhost:8546 localhost:8547',
        ],
    }


def root_command(
    test: str,
    nodes: typing.Sequence[str],
    output: str | None,
    metrics: typing.Sequence[str],
    mode: rpc_bench.LoadTestMode | None,
    rates: typing.Sequence[int] | typing.Sequence[str] | None,
    duration: int | None,
    random_seed: int | None,
    dry: bool,
    quiet: bool,
) -> None:

    # TODO: perform str conversions later in pipeline
    # if duration is not None:
    #     import tooltime

    #     duration = tooltime.timelength_to_seconds(duration)
    if rates is not None:
        rates = [int(rate) for rate in rates]

    rpc_bench.run(
        test_name=test,
        mode=mode,
        nodes=nodes,
        metrics=metrics,
        random_seed=random_seed,
        verbose=(not quiet),
        rates=rates,
        duration=duration,
        dry=dry,
        output=output,
    )

