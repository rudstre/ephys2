# Configuring CI/CD

We describe the setup (as of May 2022) for Gitlab CI/CD here since other sources of documentation, such as the docserver, are deployed using this process.

## Summary of the pipeline

Our Gitlab CI/CD configuration is located at [.gitlab-ci.yml](.gitlab-ci.yml). It uses `terraform` to provision resources on [NERC OpenStack](https://stack.nerc.mghpcc.org/dashboard/project/), such as:

* The VM, floating IP, and http server for the docserver

## Running the pipeline

The pipeline is configured to run only when manually initiated, since our project has a quota of 400 CI minutes per month.

To run the pipeline manually,

* Click **CI/CD** from the sidebar
* Click **Run pipeline**
* Select the `branch` you want to run the pipeline on (typically `master`) and run the pipeline.

## Gitlab CI/CD Variables

Several secrets & credentials are stored in as Gitlab CI/CD variables, which are exposed to the deployment pipeline at runtime. To view / edit them, do:

* Click **CI/CD** from the sidebar
* Scroll down to **Variables** and click **Expand**

When adding or editing variables, ensure the option **Protect Variable** is unchecked.

### 0. SSH keys

Generating SSH Keys:
```bash
ssh-keygen -t rsa -b 4096 -C "ephys2_gitlab_ci@g.harvard.edu"
```

The generated public-private key pair (`id_rsa` and `id_rsa.pub`) should be copied to the following **Gitlab CI/CD Variables**:

* `SSH_PRIVATE_KEY`
* `SSH_PUBLIC_KEY`

### 1. OpenStack credentials

