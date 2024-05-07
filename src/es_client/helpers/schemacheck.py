"""SchemaCheck class and associated functions"""

# pylint: disable=protected-access, broad-except
import typing as t
import logging
from re import sub
from copy import deepcopy
from voluptuous import Schema
from es_client.defaults import KEYS_TO_REDACT
from es_client.exceptions import FailedValidation


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
        self.logger = logging.getLogger(__name__)
        # Set the Schema for validation...
        self.logger.debug("Schema: %s", schema)
        if isinstance(config, dict):
            self.logger.debug('"%s" config: %s', test_what, password_filter(config))
        else:
            self.logger.debug('"%s" config: %s', test_what, config)
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

        def get_badvalue(data_string, data):
            elements = sub(r"[\'\]]", "", data_string).split("[")
            elements.pop(0)  # Get rid of data as the first element
            value = None
            for k in elements:
                try:
                    key = int(k)
                except ValueError:
                    key = k
                if value is None:
                    value = data[key]
                    # if this fails, it's caught below
            return value

        try:
            self.badvalue = get_badvalue(str(self.error).split()[-1], self.config)
        except Exception as exc:
            self.logger.error("Unable to extract value: %s", exc)
            self.badvalue = "(could not determine)"

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
            return self.schema(self.config)
        except Exception as exc:
            try:
                # pylint: disable=E1101
                self.error = exc.errors[0]
            except Exception as err:
                self.logger.error("Could not parse exception: %s", err)
                self.error = f"{exc}"
            self.parse_error()
            self.logger.error("Schema error: %s", self.error)
            raise FailedValidation(
                f"Configuration: {self.test_what}: Location: {self.location}: "
                f'Bad Value: "{self.badvalue}", {self.error}. Check configuration file.'
            ) from exc
