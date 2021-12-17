# CHAMP is an HPC Access and Metadata Portal

A web portal providing a simple interface to run packaged applications via a
high performance computing (HPC) batch system. CHAMP is designed primarily for
beginner or occasional users of HPC facilities. Integration with data
repositories supports publication of data compatible with FAIR principles.

To report bugs, request new features or provide feedback please create an issue
in this repository.

## Feature Overview

* Users create jobs by selecting from configured lists of job resources and
  software packages:

  ![A form for the initial step in job creation](docs/images/resources.png)

* Based on the selected software the user then uploads relevant files to
  complete the job submission process, e.g.:

  ![A form for file upload step in job creation](docs/images/job_files.png)

* Job outputs can be reviewed via a simple directory view or the Open OnDemand
  Files app.
* Information about software, resources and submission time along with an
  optional description are recorded for all jobs. Jobs can be filtered based on
  searchers against this data.
* Jobs are organised into collections called projects.
* User's can link the portal with supported data repositories to allow one-click
  publication of job outputs. The DOI for any publications are available within
  the portal. Publications may include rich metadata based on the software used.

## Technical Overview

CHAMP has been developed as a Passenger App within the [Open OnDemand][] (OOD)
framework. This approach allows the portal to be very simple but also portable
across a wide range of HPC infrastructure. OOD provides a consistent
programmatic interface for interacting with a number of popular HPC resource
managers. It also supports a wide range of authentication mechanisms. All portal
processes and jobs are run using the correct UID for each user.

[Open Ondemand]: https://openondemand.org/

CHAMP is written in Python (>=3.7) using [Django][]. Front-end web content is
almost exclusively HTML with very minimal use of JavaScript. Interaction with
the OOD libraries is provided via simple Ruby shims called as a sub-process.

[Django]: https://www.djangoproject.com/

Integrations with data repositories are supported via a plugin mechanism. This
allows integrations with institution-specific repositories to be developed and
deployed easily. Authentication using OAuth2 only is supported however the
provided data models may also be suitable for use with other mechanisms.

CHAMP is primarily configured via a yaml file and is extremely flexible. Use of
a templating approach means there are no restrictions on the types of computing
resources or software that can be made available. It is possible for users to
add their own configuration within relevant parts of the template. This can be
useful for e.g. providing accounting information.

## Setup Instructions

This section covers setting up CHAMP within an OpenOnDemand (OOD) instance. It
is possible to run the tests and a development version the portal outside of OOD
with limited functionality. Please see the [Development
Guide](#development-guide) section for this.

### Requirements

* A server with an Open OnDemand installation with the required cluster
  configuration completed. The filesystem where job outputs will be saved must
  be mounted and accessible to processes with expected user UIDs. The built-in
  Files app of Open OnDemand must be enabled.
* An installation of Python >= 3.7.

### Test Deployment

It's best to first deploy a version of CHAMP within the OOD development sandbox
to allow testing and refinement of the configuration. If you're not familiar
with this process its strongly recommended that you follow the [tutorial][]
provided by the OOD documentation first.

[tutorial]: https://osc.github.io/ood-documentation/latest/app-development/tutorials-passenger-apps.html

When you're ready [clone and setup][] CHAMP. Some additional configuration is
required before the app will run:

[clone and setup]: https://osc.github.io/ood-documentation/latest/app-development/tutorials-passenger-apps/ps-to-quota.html#clone-and-setup

1. Create a Python (>=3.7) virtual environment containing the dependencies for
   the portal e.g.:

   ```
   python -mvenv /var/portal_venv/
   /var/portal_venv/bin/pip install -r requirements.txt
   ```

1. Edit `/etc/ood/config/nginx_stage.yml` and add the below entry (or
   equivalent) to the `pun_custom_env` item:

   ```
   PORTAL_VENV: '/var/portal_venv/bin/python'
   ```

1. If the CHAMP source code is not on a filesystem from which jobs can be
   submitted then in the root directory create a `.env` file containing
   something like:

   ```
   JOBS_DIR=${HOME}/portal_jobs_dev
   ```

   Jobs will be stored and submitted from the specified location. You can skip
   this step in which case job files will be stored in `portal_jobs` in the same
   directory as the CHAMP source code.
1. Django's usual method for serving static files during development doesn't
   work within OOD so run the below command to have Apache serve them instead:

   ```
   /var/portal_venv/bin/python manage.py collectstatic
   ```

1. Create a minimal configuration file by taking a copy of
   `docs/example_config.yaml`. A value for the `cluster` key must be added in
   order for it to be viable. This should be the name of the cluster that the
   portal will use for job submission as configured for OOD (i.e. the file
   prefix for the cluster configuration file in `/etc/ood/config/clusters.d`).

Using this setup you should now be able to launch the portal via the development
sandbox interface. It won't be possible to run any jobs however using such a
minimal configuration. See below for details on creating a full configuration.

## Configuration

Before creating a production deployment a full configuration file must be
developed. This configuration will depend on details of your cluster so only
generic guidance is provided here. CHAMP is very flexible and you have a lot of
choice in how jobs will behave when run. An [example configuration][] as used in
production by Imperial College London is available for reference.

Reference documentation for the configuration file can be found below however
we'll start with a short overview. CHAMP generates submission scripts for jobs
via a simple template system. The primary template is provided by the
`script_template` key in the config file. Different resource and software
configurations provide lines to be inserted into the template.

Software configurations can run arbitrarily complex workflows. As a simple
example, the Imperial College [example configuration][] for Gaussian does the
following:

* Adds appropriate directives to the Gaussian input file based on job resources
* If an optional formatted checkpoint file is provided runs `unfchk` and adds
  the `OldChk` directive to the Gaussian input file
* Runs `formchk` after the job is complete.

### Configuration File Reference

All keys are required unless stated otherwise. Validation of config files is
provided by the [marshmallow][] library when CHAMP loads. This should give easy
to understand errors in the case of problems in the config file. You can also
use the script `config_validation.py` to check your config.

[marshmallow]: https://marshmallow.readthedocs.io/en/stable/

#### `config_link` (optional)

A string providing a URL linking to the current portal configuration file. This
is primarily intended for use where the configuration is made public in a git
repository (e.g. the Imperial College [example configuration][]). This allows
users of the system to provide additional software configurations according to
their needs. When this key is provided the link is added to the "Create Job"
page of the portal with the text "add a new software".

#### `cluster`

The name of the cluster that CHAMP will use for job submission as configured for
OOD (i.e. the file prefix for the cluster configuration file in
`/etc/ood/config/clusters.d`).

#### `custom_config_line_regex`

A regular expression used to validate custom configuration snippets provided by
users. Typically this will be used to limit lines to valid directives for your
scheduler, e.g. in the case of PBS this would be something like:

```
"^#PBS .*"
```

To provide no validation use `.*`.

#### `enabled_repositories`

May be empty or a list of strings indicating data repositories to which users
may publish data. To be enabled a data repository must be registered via the
repository plugin system. See the section on [Data
Repositories](#data-repositories) for details. Strings in this list should
correspond to the label attribute of the registered class. Plugins for the
following repositories are included with CHAMP:

* Zenodo (label - 'zenodo')

Once enabled it should be possible for users to link to a repository via the
Profile page. Please note that there may be extra setup steps for each
repository (see below section of Data Repositories).

#### `resources`

A list of dictionaries specifying the available resource choices for running
jobs. Each list entry corresponds to an item in the dropdown box for resources
when creating a new job. Each dictionary contains exactly 2 keys:

* `description` (string): A short human readable description of this resource
  selection. This is the text that will be displayed in the dropdown menu and
  which will be recorded when a job runs.
* `script_lines` (string): The lines that will be inserted into
  `script_template`. This should include the appropriate scheduler directives
  but it may also be useful to set environment variables that can be used in the
  template.

#### `script_template`

The main template used to generate a submission script for each job. Insertion
points are denoted by strings inside curly braces e.g. `{commands}`. The
template must meet the following criteria:

* It must set the job name by using the insertion point `{job_name}`
* Directly beneath any scheduler directives should be the line
  `{custom_config}{resources}`. Note that `{resources}` will be replaced with
  the specified scheduler directives when the template is compiled into a
  submission script.
* It should change the current working directory to the submission directory of
  the job. This should be easily referenced via the appropriate environment
  variable for your resource manager.
* When the job is running it should record the ongoing duration (in seconds) of
  the job to a file named `WALLTIME` in the job directory. The following idiom
  near the start can be included to achieve this:

  ```
  (while true; do echo $SECONDS > WALLTIME; sleep 5s; done) &
  ```

* Its final line must be `{commands}`. This is the point where the different
  script lines for each software will be added.

An example template for PBS that meets these criteria is provided below:

```
script_template: |
  #!/bin/bash
  #PBS -N {job_name}
  {custom_config}{resources}

  cd "$PBS_O_WORKDIR"

  (while true; do  echo $SECONDS > WALLTIME; sleep 5s; done) &

  {commands}
```

#### `software`

A list of dictionaries, each specifying a piece of software that can be run
using the portal. Each list entry corresponds to an item in the dropdown box for
software when creating a new job. Each dictionary contains 4 keys:

* `commands` (string): The commands to be inserted into `script_template` that
  actually run the software. Insertion points may be provided for each of the
  keys in the dictionaries specify optional and required input files. These
  insertion points will be replaced with the name of the file as uploaded by the
  user. In the case of an optional file that was not uploaded an empty string is
  substituted. The below idiom can be used to determine if an optional file was
  provided, e.g. for the optional file `file1`:

  ```
  [[ "{file1}" != "" ]] && commands if file is present
  ```

  Two additional files must be created by the commands:
  * `FILES_TO_PUBLISH`: A tab-separated file containing information about which
    files to include in any publications made to a linked data repository. The
    file must contain two columns. The first line must provide the headers
    `name` and `description`. Each following entry should give the name of the
    file to be published and a short description in the appropriate column.
  * `METADATA`: A tab-separated file containing rich metadata to include in any
    publications. The file must contain two columns. The first line must provide
    the headers `name` and `value`. Each following entry should provide the name
    of an item metadata and its value.
* `input_files` (dictionary): The input files to be provided by the end user to
  run their calculation. This dictionary must contain 2 keys, `required` and
  `optional`. Each of these in turn may be either empty or a list of
  dictionaries with the keys "key" and "description". This is most easily
  demonstrated with an example.

  ```
  input_files:
    required:
      - key: file1
        description: "human readable description of file1"
    optional:
      - key: file2
        description: "human readable description of file2"
  ```

  The above defines two input files, `file1` and `file2`, for a piece of
  software. Of these `file1` is required for a job to run whilst `file2` is
  optional. This is reflected in the form generated for users when submitting a
  job using this software. The key values `file1` and `file2` are available as
  insertion points within the body of `commands`. The human readable description
  of each file will be used as the label for the form field during upload.
* `help_text` (string): The help text made available to the user when submitting
  a job with this software. It should provide sufficient detail to enable users
  to prepare the input files for their jobs. This text is rendered as part of a
  web page and may contain html tags.
* `name` (string): The human readable name of the software. This is the text
  that will be displayed in the dropdown menu and which will be recorded when a
  job runs.

#### `external_links` (optional)

A list of dictionaries of links to external resources. These are added as items
to the banner menu at the top of the CHAMP web interface. The intended use is to
add links to resources (e.g. a service status page) that may be relevant for
individual deployments. Dictionaries should have exactly two keys - "text" and
"url". The "text" value will be displayed in the banner menu whilst "url"
provides the associated link. For example:

```
external_links:
  - text: "System Status"
    url: https://my.status.page
```

### Production Deployment

Once a suitable configuration has been developed and tested.

1. Clone a copy of the repository source code to a directory within
   `/var/www/ood/apps/sys`
1. Within the new clone, create a new file `settings/site.py`. This file will
   contain all of the Django settings required for a site specific
   deployment. Among it's imports it must have `from .production import *` to
   pick up the configuration from both `settings.py` and `production.py` in the
   same directory. See the Django documentation for full details of valid
   settings. At a minimum you will need to set values for `ALLOWED_HOSTS` and
   `ADMINS` as well as valid configuration of an SMTP server (including
   credentials if required). You can also use this file to overwrite any
   settings from `settings.py` and `production.py`. Settings for the portal that
   you may wish to override:
    * `DATABASES["default"]["name"]` - due to OOD's use of dedicated per user
      servers to run apps each user has their own sqlite3 database. The value of
      this setting determines where the database is saved. The default location
      is the file `portal_db_DO_NOT_DELETE.sqlite3` in the users home directory.
    * `JOBS_DIR` - this is the location where the portal will store data for
      jobs that it runs. Job submission is carried out from sub-directories. The
      default value is the directory `portal_jobs` in the user's home directory.
1. Create a `.env` file in the root directory of the portal source code
   containing:

   ```
   SECRET_KEY="A new randomly generated secret key"
   DJANGO_SETTINGS_MODULE="portal.settings.site"
   PORTAL_CONFIG_PATH="/path/to/your/portal_config.yaml"
   ```

CHAMP should now be launchable for all users via the OOD Dashboard as "HPC
Portal" under the Jobs category. If you've enabled the Zenodo repository please
see the below section on completing the setup steps required for this.

### Data Repositories

CHAMP supports publishing individual jobs to linked data repository
services. The DOI from the publication is recorded in the portal against the job
record. Where repositories support the full DataCite Subject schema publication
of rich metadata is also possible. The files and metadata uploaded for a record
are specified on a job-by-job basis from the contents of the `FILES_TO_PUBLISH`
and `METADATA` files in a job directory. It is expect that these files will be
created during a job according to the software being used. See the documentation
for the`software` key within the [Configuration File
Reference](#configuration-file-reference) section.

The portal ships with a Zenodo integration that can be enabled. See [Using the
Zenodo Integration](#using-the-zenodo-integration) below.

Data repository integrations are written as plugins. Any Python module placed in
`main/repositories/plugins/` will be imported. See [Developing a Repository
Plugin](#developing-a-repository-plugin) for details on writing a plugin.

#### Using the Zenodo Integration

Once enabled this integration requires the details of an developer (OAuth2)
application in order to function. This can be setup via the Zenodo website using
any valid user account but it's suggested to something institutional so that
everything looks official for end users. At time of writing an app can be
created via Settings->Applications->Developer Applications. The correct redirect
URI to use will depend on your deployment but should be the URI of the index
page suffixed with `token/zenodo`. The client type should be private.

Once created you'll need the Client ID and Client Secret in order to
proceed. With these in hand add the following entries to the `.env` file in the
root of your portal:

```
ZENODO_CLIENT_ID="your client id"
ZENODO_CLIENT_SECRET="your client secret"
```

It should now be possible for users to link to the repository (authorize the
OAuth application) and publish jobs.

#### Developing a Repository Plugin

Repository integrations are provided by concrete sub-classes of the abstract
`RepositoryBase` defined in `main/repositories/base_repository.py`. The
sub-class must also be decorated by the `register` function defined in
`main/repositories/__init__.py`.

The `RepositoryBase` abstract class was designed with OAuth2 applications in
mind and only this method is officially supported. That said the class is
flexible enough that it can be (and has been) used with other schemes. The
included Zenodo integration is a good starting point for interacting with other
OAuth2 applications.

## Development Guide

Two development setups are available for working with the portal. Firstly the
portal can be run without an installation of Open OnDemand. Alternatively a
Docker Compose configuration running a demo cluster with Open OnDemand is also
available.

### Without Open OnDemand

Needless to say when working in this way you won't be able submit jobs but the
test suite can be run. You should either create a python virtual environment and
install the dependencies from `requirements.txt` or you can use the provided
Dockerfile with Docker Compose.

Please see [CONTRIBUTING.md][] for details of the expected workflow for making
pull requests.

[CONTRIBUTING.md]: CONTRIBUTING.md

#### Run Tests

All tests can be run by using e.g.:

```
python manage.py test
```

or using Docker Compose:

```
docker-compose run app python manage.py test
```

#### Run Server

To run CHAMP locally first copy `docs/example_config.yaml` to
`portal_config.yaml` in repository root directory. Add an empty string to the
`cluster` key. This is the minimum required config to run the server. Then:

```
python manage.py runserver
```

or using Docker Compose:

```
docker-compose up
```

then point your browser to `localhost:8000`. The working tree of the repository
is mounted into the Docker container so updates to the code should be reflected
in the running server using both methods.

### Demo Cluster

Configuration is provided by a Docker Compose file in the `demo_cluster`
directory. This borrows heavily from the [ubccr/hpc-toolset-tutorial][].

[ubcrr/hpc-toolset-tutorial]: https://github.com/ubccr/hpc-toolset-tutorial

#### Run Tests

All tests, including those that perform job submission, can be run by using e.g.:

```
docker-compose -f demo_cluster/docker-compose.demo.yaml run ondemand bash demo_cluster/run_test.sh
```

#### Run Server

Start the server with:

```
docker-compose -f demo_cluster/docker-compose.demo.yaml
```

then access `https://localhost:3443/pun/sys/champ` in a browser. When prompted
for credentials use `hpcadmin` with the password `ilovelinux`.

[example configuration]: https://github.com/ImperialCollegeLondon/hpc_portal_config
