### Getting Started

## Setting up development environment

### Ubuntu
1. Run `bash setup_env.bash`
2. Copy `env.example` to `.env`

### Windows
1. Grab git bash shell for windows
2. Have python3 installed and named `python` in path
3. Have pip3 and virutalenv instlaled
4. Run git bash as administrator and execute `bash setup_env_win.bash`


Copy `env.example` in the project root to `.env`, update any values if necessary.


### Setup with Pycharm
* Settings->Project->Project Interpreter
  * Add the virtualenv in `.virtualenv` as your project interpreter
* Settings->Languages/Frameworks
  * Turn on Djagno Support 
    * Project Root: `proj/`
    * Environment Variables: `DJAGNO_SETTINGS_MODULE=settings`
    * Manage Script: `manage.py`
* Right click `proj` directoryand click "Mark as Sources"
* Run->Edit configurations
  * Make a django server

 


