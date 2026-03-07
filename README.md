# uoft-course-compass

## Setup

It's common to use a virtual environment (venv) when working on a Python project to keep it self-contained. This allows everyone working on the project to have the same package versions installed to ensure that the code works consistently across all machines. Below are some helpful commands to set up a venv.

- Set up your venv
```bash
py -m venv venv
```

- Activate the venv. You should see `(venv)` appear in your terminal after running the command. This means you're now in the venv :)
```bash
venv\Scripts\Activate.ps1  # Windows
```

```bash
source venv/bin/activate  # macOS
```

- Install all packages
```bash
pip install -r requirements.txt
```

- Save dependencies (run after you install new packages i.e. `pip install <package>`)
```bash
pip freeze > requirements.txt
```

- To deactivate the venv once done:
```bash
deactivate
```
