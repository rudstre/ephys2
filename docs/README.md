# Build ephys2 docs

Install dependencies:
```bash
pip install -r requirements.txt
```

Then run the build process:
```
make html
```

Several documents will be autogenerated (see `build_examples.py` and `build_stages.py`). If these encounter errors, update the corresponding examples or stages. 

Finally, you will see a `_build` folder. This folder contains static HTML files to be deployed to a webserver.