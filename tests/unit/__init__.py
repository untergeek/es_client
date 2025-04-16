"""Functions and classes used for tests"""

import os
import random
import shutil
import string
import tempfile
import click
from es_client.debug import debug
from es_client.defaults import LOGGING_SETTINGS
from es_client import config as cfgfn
from es_client.utils import option_wrapper, prune_nones

debug.level = 5

ONOFF = {"on": "", "off": "no-"}

DEFAULT_HOST = "http://127.0.0.1:9200"

DEFAULTCFG = "\n".join(
    ["---", "elasticsearch:", "  client:", f"    hosts: [{DEFAULT_HOST}]"]
)

EMPTYCFG = (
    "---\n"
    "elasticsearch:\n"
    "  client:\n"
    "    hosts: \n"
    "      - \n"
    "    cloud_id: \n"
)

TESTUSER = "joe_user"
TESTPASS = "password"

YAMLCONFIG = (
    "---\n"
    "elasticsearch:\n"
    "  client:\n"
    f"    hosts: [{DEFAULT_HOST}]\n"
    "  other_settings:\n"
    "    username: {0}\n"
    "    password: {1}\n"
)

click_opt_wrap = option_wrapper()


def random_directory():
    """Create a random dictionary"""
    dirname = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
    )
    directory = tempfile.mkdtemp(suffix=dirname)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


class FileTestObj(object):
    """All file tests will use this object"""

    def __init__(self):
        self.args = {}
        dirname = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        filename = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        # This will create a psuedo-random temporary directory on the machine
        # which runs the unit tests, but NOT on the machine where elasticsearch
        # is running. This means tests may fail if run against remote instances
        # unless you explicitly set `self.args['location']` to a proper spot
        # on the target machine.
        self.written_value = """NOTHING"""
        self.args["tmpdir"] = tempfile.mkdtemp(suffix=dirname)
        if not os.path.exists(self.args["tmpdir"]):
            os.makedirs(self.args["tmpdir"])
        self.args["configdir"] = random_directory()
        self.args["configfile"] = os.path.join(self.args["configdir"], "es_client.yml")
        self.args["filename"] = os.path.join(self.args["tmpdir"], filename)
        self.args["no_file_here"] = os.path.join(self.args["tmpdir"], "not_created")
        with open(self.args["filename"], "w", encoding="utf-8") as f:
            f.write(self.written_value)

    def teardown(self):
        """Default teardown"""
        if os.path.exists(self.args["tmpdir"]):
            shutil.rmtree(self.args["tmpdir"])
        if os.path.exists(self.args["configdir"]):
            shutil.rmtree(self.args["configdir"])

    def write_config(self, fname, data):
        """Write config to named file"""
        with open(fname, "w", encoding="utf-8") as f:
            f.write(data)


# pylint: disable=unused-argument, redefined-builtin, too-many-arguments
@click.command()
@click_opt_wrap(*cfgfn.cli_opts("config"))
@click_opt_wrap(*cfgfn.cli_opts("hosts"))
@click_opt_wrap(*cfgfn.cli_opts("cloud_id"))
@click_opt_wrap(*cfgfn.cli_opts("api_token"))
@click_opt_wrap(*cfgfn.cli_opts("id"))
@click_opt_wrap(*cfgfn.cli_opts("api_key"))
@click_opt_wrap(*cfgfn.cli_opts("username"))
@click_opt_wrap(*cfgfn.cli_opts("password"))
@click_opt_wrap(*cfgfn.cli_opts("bearer_auth"))
@click_opt_wrap(*cfgfn.cli_opts("opaque_id"))
@click_opt_wrap(*cfgfn.cli_opts("request_timeout"))
@click_opt_wrap(*cfgfn.cli_opts("http_compress", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("verify_certs", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("ca_certs"))
@click_opt_wrap(*cfgfn.cli_opts("client_cert"))
@click_opt_wrap(*cfgfn.cli_opts("client_key"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_hostname"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_fingerprint"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_version"))
@click_opt_wrap(*cfgfn.cli_opts("master-only", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("skip_version_test", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("loglevel", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logfile", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logformat", settings=LOGGING_SETTINGS))
@click.pass_context
def simulator(
    ctx,
    config,
    hosts,
    cloud_id,
    api_token,
    id,
    api_key,
    username,
    password,
    bearer_auth,
    opaque_id,
    request_timeout,
    http_compress,
    verify_certs,
    ca_certs,
    client_cert,
    client_key,
    ssl_assert_hostname,
    ssl_assert_fingerprint,
    ssl_version,
    master_only,
    skip_version_test,
    loglevel,
    logfile,
    logformat,
):
    """Test command with all regular options"""
    ctx.obj = {}
    cfgfn.get_config(ctx)
    cfgfn.generate_configdict(ctx)
    click.echo(f'{ctx.obj["configdict"]}')


# pylint: disable=unused-argument
@click.command()
@click_opt_wrap(*cfgfn.cli_opts("config"))
@click_opt_wrap(*cfgfn.cli_opts("hosts"))
@click_opt_wrap(*cfgfn.cli_opts("cloud_id"))
@click_opt_wrap(*cfgfn.cli_opts("api_token"))
@click_opt_wrap(*cfgfn.cli_opts("id"))
@click_opt_wrap(*cfgfn.cli_opts("api_key"))
@click_opt_wrap(*cfgfn.cli_opts("username"))
@click_opt_wrap(*cfgfn.cli_opts("password"))
@click_opt_wrap(*cfgfn.cli_opts("bearer_auth"))
@click_opt_wrap(*cfgfn.cli_opts("opaque_id"))
@click_opt_wrap(*cfgfn.cli_opts("request_timeout"))
@click_opt_wrap(*cfgfn.cli_opts("http_compress", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("verify_certs", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("ca_certs"))
@click_opt_wrap(*cfgfn.cli_opts("client_cert"))
@click_opt_wrap(*cfgfn.cli_opts("client_key"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_hostname"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_fingerprint"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_version"))
@click_opt_wrap(*cfgfn.cli_opts("master-only", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("skip_version_test", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("loglevel", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logfile", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logformat", settings=LOGGING_SETTINGS))
@click.pass_context
def default_config_cmd(
    ctx,
    config,
    hosts,
    cloud_id,
    api_token,
    id,
    api_key,
    username,
    password,
    bearer_auth,
    opaque_id,
    request_timeout,
    http_compress,
    verify_certs,
    ca_certs,
    client_cert,
    client_key,
    ssl_assert_hostname,
    ssl_assert_fingerprint,
    ssl_version,
    master_only,
    skip_version_test,
    loglevel,
    logfile,
    logformat,
):
    """Test command with all regular options"""
    # Build config file
    file_obj = FileTestObj()
    file_obj.write_config(
        file_obj.args["configfile"], YAMLCONFIG.format(TESTUSER, TESTPASS)
    )
    # User config file
    ctx.obj = {"default_config": file_obj.args["configfile"]}
    cfgfn.get_config(ctx)
    # Teardown config file
    file_obj.teardown()
    # Finish the function
    cfgfn.generate_configdict(ctx)
    click.echo(f'{ctx.obj["configdict"]}')


@click.command()
@click_opt_wrap(*cfgfn.cli_opts("config"))
@click_opt_wrap(*cfgfn.cli_opts("hosts"))
@click_opt_wrap(*cfgfn.cli_opts("cloud_id"))
@click_opt_wrap(*cfgfn.cli_opts("api_token"))
@click_opt_wrap(*cfgfn.cli_opts("id"))
@click_opt_wrap(*cfgfn.cli_opts("api_key"))
@click_opt_wrap(*cfgfn.cli_opts("username"))
@click_opt_wrap(*cfgfn.cli_opts("password"))
@click_opt_wrap(*cfgfn.cli_opts("bearer_auth"))
@click_opt_wrap(*cfgfn.cli_opts("opaque_id"))
@click_opt_wrap(*cfgfn.cli_opts("request_timeout"))
@click_opt_wrap(*cfgfn.cli_opts("http_compress", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("verify_certs", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("ca_certs"))
@click_opt_wrap(*cfgfn.cli_opts("client_cert"))
@click_opt_wrap(*cfgfn.cli_opts("client_key"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_hostname"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_assert_fingerprint"))
@click_opt_wrap(*cfgfn.cli_opts("ssl_version"))
@click_opt_wrap(*cfgfn.cli_opts("master-only", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("skip_version_test", onoff=ONOFF))
@click_opt_wrap(*cfgfn.cli_opts("loglevel", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logfile", settings=LOGGING_SETTINGS))
@click_opt_wrap(*cfgfn.cli_opts("logformat", settings=LOGGING_SETTINGS))
@click.pass_context
def simulate_override_client_args(
    ctx,
    config,
    hosts,
    cloud_id,
    api_token,
    id,
    api_key,
    username,
    password,
    bearer_auth,
    opaque_id,
    request_timeout,
    http_compress,
    verify_certs,
    ca_certs,
    client_cert,
    client_key,
    ssl_assert_hostname,
    ssl_assert_fingerprint,
    ssl_version,
    master_only,
    skip_version_test,
    loglevel,
    logfile,
    logformat,
):
    """Test command with all regular options"""
    ctx.obj = {}
    cfgfn.get_config(ctx)
    cfgfn.get_arg_objects(ctx)
    # Manual override
    ctx.obj["client_args"].hosts = None
    cfgfn.override_client_args(ctx)
    ctx.obj["configdict"] = {
        "elasticsearch": {
            "client": prune_nones(ctx.obj["client_args"].toDict()),
            "other_settings": prune_nones(ctx.obj["other_args"].toDict()),
        }
    }
    click.echo(f'{ctx.obj["configdict"]}')
