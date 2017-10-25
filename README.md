# certified-blueprint_kubernetes
This is a reference TOSCA blueprint for creating a Kubernetes cluster.  This blueprint is based in part on https://github.com/cloudify-examples/simple-kubernetes-blueprint, though heavily modified to use kubespray, control for orchestrating a kubernetes cluster.

This is a work in progress, and future commits will add features for reliability and management, as well as support for additional deployment environments. 

----
Copyright 2017, Risk Focus, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at 
http://www.apache.org/licenses/LICENSE-2.0. A copy of this [LICENSE](https://github.com/riskfocus/certified-blueprint_kubernetes/blob/master/LICENSE)
is also included in this repository.

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

Based on work by [GigaSpaces](https://github.com/cloudify-examples/simple-kubernetes-blueprint)
Author: Peter Meulbroek; Significant contribtions to this effort by Pavels Veretennikovs (rfvermut) and Edward Liu (edwick).  

----

Pre-requisites / assumptions
===
TODO: installed CM, 
VPC (10.0.0.0/8), subnets 
AWS credentials
All work is done in `us-east-1` region.

Install CLI tools
===
```bash
pip install -U cloudify
```

Connect
===
```bash
export CFY_M=<YOUR_CLOUDIFY_MANGAER_IP>
cfy profile use ${CFY_M} -u admin -p admin -t default_tenant --profile-name edge1

```

SSH Keys
===
```ssh centos@$CFY_M

# sudo -su cfyuser
# ssh-keygen
... should create keypair in /etc/cloudify/.ssh/
# cat /etc/cloudify/.ssh/id_rsa.pub
```


Pre-config
===
```bash
cfy plugins upload http://repository.cloudifysource.org/cloudify/wagons/cloudify-aws-plugin/1.5/cloudify_aws_plugin-1.5-py27-none-linux_x86_64-centos-Core.wgn
cfy plugins upload http://repository.cloudifysource.org/cloudify/wagons/cloudify-fabric-plugin/1.5/cloudify_fabric_plugin-1.5-py27-none-linux_x86_64-centos-Core.wgn
cfy plugins upload https://github.com/cloudify-incubator/cloudify-utilities-plugin/releases/download/1.2.5/cloudify_utilities_plugin-1.2.5-py27-none-linux_x86_64-centos-Core.wgn
cfy plugins upload http://repository.cloudifysource.org/cloudify/wagons/cloudify-fabric-plugin/1.5/cloudify_fabric_plugin-1.5-py27-none-linux_x86_64-centos-Core.wgn
```

Secrets
```bash
cfy secrets create ec2_region_endpoint -s ec2.us-east-1.amazonaws.com
cfy secrets create ec2_region_name -s us-east-1
cfy secrets create aws_secret_access_key ...from IAM...
cfy secrets create aws_access_key_id ...from IAM...
cfy secrets create agent_key_private -s /etc/cloudify/.ssh/id_rsa
cfy secrets create agent_key_public -s "ssh-rsa AAAA...generate..in..step..above... TvQ8buB cfyuser@cloudify"
```

k8 cluster
===
```bash
cfy install aws-blueprint.yaml -i inputs/ --include-logs --timeout 9000 -b k8.cluster
cfy deployment outputs k8.cluster
```
Note one of the kubernetes_master_private_ip (e.g. 10.0.4.31)

