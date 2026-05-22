## Getting Started

### Prerequisites

Ensure you have Python 3.10+ installed on your system before proceeding. To check if you have Python installed, run the following command in your terminal:

```
python --version
```

On macOS/Linux, you may need to use:

```
python3 --version
```

If Python is installed, this will print the version number (e.g. `Python 3.11.2`). If not, download and install it from [python.org](https://www.python.org/downloads/) before continuing.
### Setting Up the Virtual Environment

> **All commands in this section must be run from the `backend` directory.** Navigate there first:
> ```
> cd backend
> ```

It is recommended to use a virtual environment to manage project dependencies in isolation and avoid version conflicts with other projects.

A virtual environment creates an isolated Python environment for this project. This means all dependencies are installed locally within the project folder rather than globally on your machine, preventing version conflicts with other Python projects you may have.

**1. Create the virtual environment**

Run the command for your operating system:

| Platform | Command |
|---|---|
| Windows | `python -m venv .venv` |
| macOS / Linux / WSL | `python3 -m venv .venv` |

> **Ubuntu / WSL users:** If you get an error about `ensurepip` not being available, first check your Python version:
> ```
> python3 --version
> ```
> Then run the following, replacing `3.10` with your version (e.g. `3.11`, `3.12`):
> ```
> rm -rf .venv
> sudo apt install python3.10-venv
> python3 -m venv .venv
> ```

**2. Activate the virtual environment**

Choose the command that matches your operating system and shell:

| Platform | Shell | Command |
|---|---|---|
| Windows | Command Prompt | `.venv\Scripts\activate` |
| Windows | PowerShell | `.\.venv\Scripts\Activate.ps1` |
| macOS / Linux | bash / zsh | `source .venv/bin/activate` |

Once activated, your terminal prompt will be prefixed with `(.venv)`, confirming the environment is active.

**3. Install dependencies**

Once the virtual environment is activated, you are ready to install the project dependencies. Dependencies are the external packages the project relies on to run, such as FastAPI, SQLAlchemy, Celery, and Redis. They are listed in the `requirements` files and installed using `pip`, Python's package installer.

The project uses two dependency files:

- `requirements.txt` - contains only the packages needed to run the application. This is what gets installed on the production server (EC2).
- `requirements-dev.txt` - contains everything in `requirements.txt` plus additional tools used during development and testing (`pytest`, `black`, `ruff`). This is what you install locally and what CI uses to run automated tests.

If you are a team member setting up your local environment, or if you are configuring CI, run:

```
pip install -r requirements-dev.txt
```

If you are setting up the production server (EC2) only, run:

```
pip install -r requirements.txt
```

> **Note:** Remember to activate the virtual environment every time you open a new terminal session before running any commands. Your `.venv` only needs to be created once, but it must be activated each session.

> **To deactivate the virtual environment** when you are done, simply run:
> ```
> deactivate
> ```
> This works the same on all platforms. Your prompt will return to normal, confirming the environment is no longer active.