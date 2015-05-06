import re
from .utils import get_pref, get_project_pref, get_quotes
from .utils import get_jscs_options, strip_snippet_groups


class RequireSnippet():

    """Class to create snippet to insert for require statement"""

    def __init__(self, name, path,
                 should_add_var, should_add_var_statement,
                 context_allows_semicolon,
                 view=None,
                 file_name=None):
        self.view = view
        self.name = name
        self.path = path
        self.should_add_var = should_add_var
        self.should_add_var_statement = should_add_var_statement
        self.context_allows_semicolon = context_allows_semicolon
        self.es6import = self.get_project_pref('import')
        self.var_type = self.get_project_pref('var')
        if self.var_type not in ('var', 'const', 'let'):
            self.var_type = 'var'
        self.file_name = file_name
        self.jscs_options = dict()
        if self.file_name:
            self.jscs_options = get_jscs_options(self.file_name)

    def get_formatted_code(self):
        should_use_snippet = self.should_use_snippet()
        should_add_semicolon = self.should_add_semicolon()
        should_strip_setter_whitespace = self.should_strip_setter_whitespace()
        promisify = self.promisify()
        require_fmt = 'require({quote}{path}{quote})'
        import_fmt = 'import ${{1:{name}}}'
        import_fmt += ' from {quote}{path}{quote}'

        if promisify:
            require_fmt = '%s(%s)' % (promisify, require_fmt)

        if self.should_add_var:
            require_fmt = '${{1:{name}}} = ' + require_fmt
            if self.should_add_var_statement:
                require_fmt = self.var_type + ' ' + require_fmt

        if should_add_semicolon:
            import_fmt += ';'
            require_fmt += ';'

        if should_strip_setter_whitespace['before']:
            require_fmt = re.sub(' =', '=', require_fmt)

        if should_strip_setter_whitespace['after']:
            require_fmt = re.sub('= ', '=', require_fmt)

        fmt = import_fmt if self.es6import else require_fmt

        if not should_use_snippet:
            fmt = strip_snippet_groups(fmt)

        return fmt.format(
            name=self.name,
            path=self.path,
            quote=self.get_quotes()
        )

    def get_args(self):
        return {
            'contents': self.get_formatted_code()
        }

    def get_quotes(self):
        """Allow explicit validateQuoteMarks rules to
        override the quote preferences"""
        # However ignore the 'true' autodetection setting.
        jscs_quotes = self.jscs_options.get('validateQuoteMarks')
        if isinstance(jscs_quotes, dict):
            jscs_quotes = jscs_quotes.get('mark')
        if jscs_quotes and jscs_quotes is not True:
            return jscs_quotes

        # Use whatever quote type is set in preferences
        return get_quotes()

    def promisify(self):
        if not self.get_project_pref('usePromisify'):
            return

        if self.path in self.get_project_pref('promisify'):
            return self.get_project_pref('promise').get('promisify')

        if self.path in self.get_project_pref('promisifyAll'):
            return self.get_project_pref('promise').get('promisifyAll')

        return None

    def should_add_semicolon(self):
        # Ignore semicolons when jscs options say to
        if self.jscs_options.get('disallowSemicolons', False):
            return False

        if get_pref('semicolon_free'):
            return False

        return self.context_allows_semicolon

    def should_strip_setter_whitespace(self):
        """Parses the disallowSpace{After,Before}BinaryOperators
        jscs options and checks if spaces are not allowed before or
        after an `=` so we know if we should strip those from the
        var statement.
        """

        def parse_jscs_option(val):
            if type(val) == bool:
                return val

            if isinstance(val, list) and '=' in val:
                return True

            return False

        return dict(
            before=parse_jscs_option(
                self.jscs_options.get('disallowSpaceBeforeBinaryOperators')),
            after=parse_jscs_option(
                self.jscs_options.get('disallowSpaceAfterBinaryOperators'))
        )

    def should_use_snippet(self):
        return get_pref('snippet')

    def get_project_pref(self, key):
        return get_project_pref(key, view=self.view)
