"""SchemaCheck class and associated functions"""
# pylint: disable=protected-access, broad-except
import logging
from re import sub
from copy import deepcopy
from es_client.defaults import KEYS_TO_REDACT
from es_client.exceptions import ConfigurationError

def password_filter(data):
    """
    Return a deepcopy of the dictionary with any password fields hidden
    """
    def iterdict(mydict):
        for key, value in mydict.items():
            if isinstance(value, dict):
                iterdict(value)
            elif key in KEYS_TO_REDACT:
                mydict.update({key: "REDACTED"})
        return mydict
    return iterdict(deepcopy(data))

class SchemaCheck(object):
    """
    Validate ``config`` with the provided :py:class:`~.voluptuous.schema_builder.Schema`.
    ``test_what`` and ``location`` are for reporting the results, in case of
    failure.  If validation is successful, the method returns ``config`` as
    valid through the :py:meth:`~.es_client.helpers.schemacheck.SchemaCheck.result` method.

    :param config: A configuration dictionary.
    :param schema: A voluptuous schema definition
    :param test_what: which configuration block is being validated
    :param location: An string to report which configuration sub-block is being tested.

    :type config: dict
    :type schema: :py:class:`~.voluptuous.schema_builder.Schema`
    :type test_what: str
    :type location: str
    """
    def __init__(self, config, schema, test_what, location):

        self.logger = logging.getLogger(__name__)
        # Set the Schema for validation...
        self.logger.debug('Schema: %s', schema)
        self.logger.debug('"%s" config: %s', test_what, password_filter(config))
        self.config = config
        self.schema = schema
        self.test_what = test_what
        self.location = location
        self.badvalue = 'no bad value yet'
        self.error = 'No error yet'

    def __parse_error(self):
        """
        Report the error, and try to report the bad key or value as well.
        """
        def get_badvalue(data_string, data):
            elements = sub(r'[\'\]]', '', data_string).split('[')
            elements.pop(0) # Get rid of data as the first element
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
            self.logger.error('Unable to extract value: %s', exc)
            self.badvalue = '(could not determine)'

    def result(self):
        """
        Return the result of the Schema test, if successful.
        Otherwise, raise a :class:`ConfigurationError <es_client.exceptions.ConfigurationError>`
        """
        try:
            return self.schema(self.config)
        except Exception as exc:
            try:
                # pylint: disable=E1101
                self.error = exc.errors[0]
            except Exception as err:
                self.logger.error('Could not parse exception: %s', err)
                self.error = f'{exc}'
            self.__parse_error()
            self.logger.error('Schema error: %s', self.error)
            raise ConfigurationError(
                f'Configuration: {self.test_what}: Location: {self.location}: '
                f'Bad Value: "{self.badvalue}", {self.error}. Check configuration file.'
            ) from exc
