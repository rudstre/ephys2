# Workflow tests

This folder contains up-to-date workflow configuration which should always pass tests defined in `workflow-tests`.

Specify variables which should be set by tests using CAPITAL LETTERS, for readability.

```yaml
- input.rhd2000:
    sessions: SET_ME # Path to RHD file
    batch_size: 100000 # Number of samples to load into memory (upper-bounded by stop_sample - stop_sample)
    batch_overlap: 0 
    aux_channels: []
```