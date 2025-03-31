"""SchemaCheck class and associated functions"""

# pylint: disable=E1101,protected-access, broad-except
import typing as t
import logging
from re import sub
from copy import deepcopy
from voluptuous import Schema
import tiered_debug as debug
from es_client.defaults import KEYS_TO_REDACT
from es_client.exceptions import FailedValidation

logger = logging.getLogger(__name__)


def password_filter(data: t.Dict) -> t.Dict:
    """
    :param data: Configuration data

    :returns: A :py:class:`~.copy.deepcopy` of `data` with the value obscured by
        ``REDACTED`` if the key is one of
        :py:const:`~.es_client.defaults.KEYS_TO_REDACT`.

    Recursively look through all nested structures of `data` for keys from
    :py:const:`~.es_client.defaults.KEYS_TO_REDACT` and redact the value with
    ``REDACTED``
    """

    def iterdict(mydict):
        for key, value in mydict.items():
            if isinstance(value, dict):
                iterdict(value)
            elif key in KEYS_TO_REDACT:
                mydict.update({key: "REDACTED"})
        return mydict

    return iterdict(deepcopy(data))


class SchemaCheck:
    """
    :param config: A configuration dictionary.
    :param schema: A voluptuous schema definition
    :param test_what: which configuration block is being validated
    :param location: An string to report which configuration sub-block is being tested.

    :type config: dict
    :type schema: :py:class:`~.voluptuous.schema_builder.Schema`
    :type test_what: str
    :type location: str

    Validate `config` with the provided :py:class:`~.voluptuous.schema_builder.Schema`.
    :py:attr:`~.es_client.helpers.schemacheck.SchemaCheck.test_what` and
    :py:attr:`~.es_client.helpers.schemacheck.SchemaCheck.location` are used for
    reporting in case of failure.  If validation is successful, the
    :py:meth:`~.es_client.helpers.schemacheck.SchemaCheck.result` method returns
    :py:attr:`~.es_client.helpers.schemacheck.SchemaCheck.config`.
    """

    def __init__(self, config: t.Dict, schema: Schema, test_what: str, location: str):
        # Set the Schema for validation...
        debug.lv2('Starting function...')
        debug.lv5(f'Schema: {schema}')
        if isinstance(config, dict):
            debug.lv5(f'"{test_what} config: {password_filter(config)}"')
        else:
            debug.lv5(f'"{test_what} config: {config}"')
        #: Object attribute that gets the value of param `config`
        self.config = config
        #: Object attribute that gets the value of param `schema`
        self.schema = schema
        #: Object attribute that gets the value of param `test_what`
        self.test_what = test_what
        #: Object attribute that gets the value of param `location`
        self.location = location
        #: Object attribute that is initialized with the value ``no bad value yet``
        self.badvalue = "no bad value yet"
        #: Object attribute that is initialized with the value ``No error yet``
        self.error = "No error yet"

    def parse_error(self) -> t.Any:
        """
        Report the error, and try to report the bad key or value as well.
        """
        debug.lv2('Starting function...')

        def get_badvalue(data_string, data):
            debug.lv5('Starting nested function...')
            elements = sub(r"[\'\]]", "", data_string).split("[")
            elements.pop(0)  # Get rid of data as the first element
            value = None
            for k in elements:
                try:
                    debug.lv4('TRY: parsing key')
                    key = int(k)
                except ValueError:
                    key = k
                if value is None:
                    value = data[key]
                    # if this fails, it's caught below
            debug.lv5(f'Exiting nested function, returning {value}')
            return value

        try:
            debug.lv4('TRY: parsing error')
            self.badvalue = get_badvalue(str(self.error).split()[-1], self.config)
        except Exception as exc:
            logger.error(f'Unable to extract value: {exc}')
            self.badvalue = "(could not determine)"
        debug.lv3('Exiting function')

    def result(self) -> Schema:
        """
        :rtype: Schema
        :returns: :py:attr:`~.es_client.helpers.schemacheck.SchemaCheck.config`

        If validation is successful, return the value of
        :py:attr:`~.es_client.helpers.schemacheck.SchemaCheck.config`

        If unsuccessful, try to parse the error in
        :py:meth:`~.es_client.helpers.schemacheck.SchemaCheck.parse_error` and raise a
        :py:exc:`FailedValidation <es_client.exceptions.FailedValidation>` exception.
        """
        try:
            debug.lv4('TRY: validating configuration...')
            return self.schema(self.config)
        except Exception as exc:
            try:
                debug.lv4('TRY: parsing exception...')
                self.error = exc.errors[0]
            except Exception as err:
                logger.error(f'Could not parse exception: {err}')
                self.error = f"{exc}"
            self.parse_error()
            logger.error(f'Schema error: {self.error}')
            msg = (
                f"Configuration: {self.test_what}: Location: {self.location}: "
                f'Bad Value: "{self.badvalue}", {self.error}. Check configuration file.'
            )
            debug.lv3('Exiting function, raising exception')
            debug.lv5(f'Value = "{exc}"')
            logger.error(msg)
            raise FailedValidation(msg) from exc
