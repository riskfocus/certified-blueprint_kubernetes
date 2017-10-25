#!/usr/bin/env python

import subprocess
import shlex
from cloudify import ctx as untyped_ctx
from cloudify.context import CloudifyContext
from cloudify.exceptions import OperationRetry

ctx = untyped_ctx  # type: CloudifyContext


def execute_command(_command):
    ctx.logger.debug('_command {0}.'.format(_command))

    subprocess_args = {
        'args': shlex.split(_command),
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    ctx.logger.debug('subprocess_args {0}.'.format(subprocess_args))

    process = subprocess.Popen(**subprocess_args)
    output, error = process.communicate()

    ctx.logger.debug('command: {0} '.format(_command))
    ctx.logger.debug('output: {0} '.format(output))
    ctx.logger.debug('error: {0} '.format(error))
    ctx.logger.debug('process.returncode: {0} '.format(process.returncode))

    if process.returncode:
        ctx.logger.error('Running `{0}` returns error.'.format(_command))
        return False

    return output


if __name__ == '__main__':
    myname = ctx.instance.id
    execute_command('rm -rf venv{}'.format(myname))
