#!/usr/bin/env python
import os
from jinja2 import Environment
import subprocess
import shlex
from cloudify import ctx as untyped_ctx
from cloudify.context import CloudifyContext
from cloudify.exceptions import OperationRetry

ctx = untyped_ctx  # type: CloudifyContext

ANSIBLE_INVENTORY = '''[kube-master]
{%- for item in masters %}
{{ item[0] }}
{%- endfor %}

[all]
{%- for item in masters + nodes + etcd %}
{{ item[0] }}             {{ item[1] }} {{ item[2] }}
{%- endfor %}

[k8s-cluster:children]
kube-node
kube-master

[kube-node]
{%- for item in nodes %}
{{ item[0] }}
{%- endfor %}

[etcd]
{%- for item in etcd %}
{{ item[0] }}
{%- endfor %}
'''


def render_inventory(**kwargs):
    return Environment().from_string(ANSIBLE_INVENTORY).render(kwargs)


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
        ctx.logger.error('Output text: "{0}"'.format(output))
        ctx.logger.error('Error text: "{0}"'.format(error))
        return False

    return output


def create_virtualenv(basename):
    venv_name = 'venv{}'.format(basename)
    execute_command('virtualenv --system-site-packages {}'.format(venv_name))
    return venv_name


def download_and_install_packages():
    output_dir = '.kube'
    execute_command('./bin/pip install kubespray')
    kubespray_tag = ctx.node.properties.get('kubespray_tag', 'v2.2.0') # v2.2.0 is current as of this writing
    execute_command('git clone -b {} https://github.com/kubernetes-incubator/kubespray.git {}'.format(kubespray_tag,
                                                                                                      output_dir))
    execute_command('./bin/pip install -r {}/requirements.txt'.format(output_dir))
    return output_dir

def create_clean_hostname(base_hostname):
    new_hostname = base_hostname.replace('_','-')
    return new_hostname

def build_inventory_file():
    nodes = [x.target.instance.host_ip for x in ctx.instance.relationships if
             x.target.instance.runtime_properties.get('KUBERNETES_NODE', False)]

    masters = [x.target.instance.host_ip for x in ctx.instance.relationships if
               x.target.instance.runtime_properties.get('KUBERNETES_MASTER', False)]

    ctx.logger.info("masters " + str(masters))
    ctx.logger.info("nodes " + str(nodes))

    inventory_cfg = 'inventory/inventory.cfg'
    os_friendly_hostname = create_clean_hostname(myname)
    with open(inventory_cfg, 'w') as f:
        f.write(render_inventory(
            # Kubespray via Cloudify/OpenStack/Ubuntu seems to require this "ip" setting in addition to
            # ansible_ssh_host. Without it, you get errors that say:
            # The error was: 'dict object' has no attribute 'ansible_default_ipv4'
            # This does not happen via command line, but since the additional "ip" setting shouldn't
            # harm the deploy, we should be OK. You can add "ansible_default_ipv4.address" to the
            # inventory.cfg file if you have access to the floating IP address.
            masters=[('{}-master{}'.format(os_friendly_hostname, idx),
                      'ansible_ssh_host={}'.format(ip),
                      'ip={}'.format(ip))
                     for idx, ip in enumerate(masters)],
            etcd=[('{}-master{}'.format(os_friendly_hostname, idx),
                   'ansible_ssh_host={}'.format(ip),
                   'ip={}'.format(ip))
                  for idx, ip in enumerate(masters)],
            nodes=[('{}-node{}'.format(os_friendly_hostname, idx),
                    'ansible_ssh_host={}'.format(ip),
                      'ip={}'.format(ip))
                   for idx, ip in enumerate(nodes)],
        ))

    execute_command('cat ' + inventory_cfg)


if __name__ == '__main__':
    # Add any custom environment variable settings that are required to support your cloud provider
    # or OS combination (e.g., OpenStack credentials)
    custom_env_settings = ctx.node.properties.get('custom_env', {})
    for next_key,next_env_setting in custom_env_settings.iteritems():
        os.environ[next_key] = next_env_setting

    myname = ctx.instance.id
    virtual_env_name = create_virtualenv(myname)
    os.chdir(virtual_env_name)

    kubespray_dir = download_and_install_packages()

    os.chdir(kubespray_dir)

    build_inventory_file()

    bootstrap_os = ctx.node.properties.get('bootstrap_os', 'centos')
    cloud_provider = ctx.node.properties.get('cloud_provider', 'aws')
    if cloud_provider.lower() != 'none':
        cloud_cmd = '-e cloud_provider={0}'.format(cloud_provider)
    else:
        cloud_cmd = ''
    network_plugin = ctx.node.properties.get('network_plugin', 'weave')
    api_server_node_port_range = ctx.node.properties.get('api_server_node_port_range', '30-37500')
    ansible_cmd = ' '.join(['../bin/ansible-playbook -i inventory/inventory.cfg cluster.yml -v -b',
                           '--private-key={0}'.format(ctx.node.properties['private_key_path']),
                           '-u {0}'.format(ctx.node.properties['agent_user']),
                           '-e bootstrap_os={0}'.format(bootstrap_os),
                           cloud_cmd,
                           '-e kube_network_plugin={0}'.format(network_plugin),
                           '-e deploy_netchecker=true',
                           '-e efk_enabled=true',
                           '-e helm_enabled=true',
                           '-e kube_apiserver_node_port_range={}'.format(api_server_node_port_range)])
    if not execute_command(ansible_cmd):
        raise OperationRetry("kubespray deploy didn't succeed")
