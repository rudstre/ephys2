# Terraform-managed NERC deployment 

## Generate SSH keypair

```console
$ ssh-keygen -t rsa -b 4096
$ export NERC_SSH_KEY=~/.ssh/nerc_ssh
```
Name it `nerc_ssh`.

## Install tools

1. Install [Terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli)
2. (Make sure you have an updated Python environment.) Install [OpenStack CLI](https://docs.openstack.org/newton/user-guide/common/cli-install-openstack-command-line-clients.html).

## Obtain OpenStack credentials

This repository does not contain credentials necessary to orchestrate NERC. Therefore, if you have not done so already, follow the instructions [here](https://github.com/nerc-project/terraform-nerc#how-to-get-credential-to-connect-nercs-openstack) to obtain a `*-openrc.sh` file containing credentials.

Log in to [NERC OpenStack](https://stack.nerc.mghpcc.org). (Click `Login via OpenID Connect`, choose `Harvard` as the provider.)

**Do not commit this file to the repository.** Run 
```console
$ source *-openrc.sh
```
to load the credentials into your environment. You may optionally add the following lines:
```bash
export GODEBUG=asyncpreemptoff=1; # For issues on mac M1
export NERC_SSH_KEY=~/.ssh/nerc_ssh # Add the relevant SSH key
```

## Provision infrastructure with Terraform 
Initialize the terraform backend using
```console
$ terraform init
```
Verify the backend exists using
```console
$ openstack container list
+-------------------------+
| Name                    |
+-------------------------+
| terraform-state         |
| terraform-state-archive |
+-------------------------+
```
Then verify the Terraform changes using 
```console
$ terraform plan
```
Finally, run 
```console
$ terraform apply
...
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

docserver_ip = "199.94.60.144"
```

## Provision applications
Running the below, you should see:
```console
$ ./provision.sh
...
Docserver started at 199.94.60.144
```

## (Optional) Logging in to the server
Using the IP address and SSH private key generated from earlier steps,
```console
$ export NERC_DOCS_IP=$(terraform output docserver_ip | tr -d '"')
$ ssh ubuntu@$NERC_DOCS_IP -i $NERC_SSH_KEY
```

## (Optional) Destroy resources
```console
$ terraform destroy
```
