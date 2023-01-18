"""SchemaCheck class and associated functions"""
# pylint: disable=protected-access, broad-except
import logging
from re import sub
from es_client.exceptions import ConfigurationError

class SchemaCheck(object):
    """
    Validate ``config`` with the provided :class:`voluptuous.Schema <voluptuous.schema_builder.Schema>`.
    ``test_what`` and ``location`` are for reporting the results, in case of
    failure.  If validation is successful, the method returns ``config`` as
    valid through the :func:`~es_client.helpers.schemacheck.SchemaCheck.result` method.

    :arg config: A configuration dictionary.
    :type config: dict
    :arg schema: A voluptuous schema definition
    :type schema: :class:`voluptuous.schema_builder.Schema`
    :arg test_what: which configuration block is being validated
    :type test_what: str
    :arg location: An string to report which configuration sub-block is
        being tested.
    :type location: str
    """
    def __init__(self, config, schema, test_what, location):

        self.logger = logging.getLogger(__name__)
        # Set the Schema for validation...
        self.logger.debug('Schema: %s', schema)
        self.logger.debug('"%s" config: %s', test_what, config)
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
                if value == None:
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
