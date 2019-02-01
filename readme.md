### Getting Started

## Setting up development environment

### Docker Environment (Preferred, all OS)
Update: 2/1/2019: Support for dockerized container added.
1. Install docker/docker-compose
2. copy env.example to .env
3. In project root do `docker-compose build`
4. Once built, migrate: `docker-compose run app migrate`
5. Bring stack up: `docker-compose run app migrate`

#### To Run Commands in Docker:
* Django Shell:
  * `docker-compose run app python proj/manage.py shell`
* DB Migrate:
  * `docker-compose run app python proj/manage.py migrate`
* Run management Command:
  * `docker-compose run app python proj/manage.py <COMMAND>`

#### Integrating Dockerized ENV with Pycharm
1. In Project -> Project Interpreter set Project Interpreter to Docker.
2. Build, Execution, Deployment -> Docker -> Add A docker environment.
3. For Debug: Add: Run -> Edit Configurations; Edit your configuration to use docker.
 * If configuration doesn't work with django server, just do it as a python command proj/`manage.py runserver 0.0.0.0:8000`

It should run everything in containers now.

### Virtualenv (Unix/Bash)
1. Run `bash setup_env.bash`
2. Copy `env.example` to `.env`

### Windows (github git bash emulator)
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
