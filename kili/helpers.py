"""
Helpers for GraphQL Queries and Mutations
"""

from typing import Optional
import base64
import functools
from json import dumps, loads
import re
import warnings
import mimetypes
import pyparsing as pp

import requests

from kili.exceptions import EndpointCompatibilityError, GraphQLError


class Compatible():
    """
    Compatibility of Kili Python SDK version with Kili API version
    """

    # pylint: disable=dangerous-default-value
    def __init__(self, endpoints=['v1']):
        self.endpoints = endpoints
        self.version_extractor = re.compile(r'\/v\d+/')
        self.address_extractor = re.compile(r':400\d+/')

    def client_is_compatible(self, endpoint: str):
        """
        Checks if client is compatible with Kili API

        Args:
            endpoint: the Kili API endpoint
        """
        version_matched = self.version_extractor.search(endpoint)
        address_matched = self.address_extractor.search(endpoint)
        if not version_matched and not address_matched:
            return False
        if address_matched:
            version = 'v1' if address_matched.group() == ':4000/' else 'v2'
        if version_matched:
            version = 'v1' if version_matched.group() == '/v1/' else 'v2'
        return version in self.endpoints

    def __call__(self, resolver, *args, **kwargs):
        @functools.wraps(resolver)
        def checked_resolver(*args, **kwargs):
            try:
                client_endpoint = args[0].auth.client.endpoint
            except Exception as exception:
                raise ValueError(
                    'Cannot find client endpoint from resolver'
                    f' {resolver.__name__} with arguments {args}') from exception
            if self.client_is_compatible(client_endpoint):
                return resolver(*args, **kwargs)
            raise EndpointCompatibilityError(
                resolver.__name__, client_endpoint)
        return checked_resolver


def format_result(name, result, _object=None):
    """
    Formats the result of the GraphQL queries.

    Args:
        name: name of the field to extract, usually data
        result: query result to parse
    """
    if 'errors' in result:
        raise GraphQLError(name, result['errors'])
    formatted_json = format_json(result['data'][name])
    if _object is None:
        return formatted_json
    if isinstance(formatted_json, list):
        return [_object(element) for element in formatted_json]
    return _object(formatted_json)


def content_escape(content):
    """
    Escapes the content

    Args:
        content: string to escape
    """
    return content.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')


def get_data_type(path):
    """
    Get the data type, either image/png or application/pdf

    Args:
        path: path of the file
    """
    mime_type, _ = mimetypes.guess_type(path.lower())
    return mime_type if mime_type else ''


def encode_base64(path):
    """
    Encode a file in base 64

    Args:
        path: path of the file
    """
    data_type = get_data_type(path)
    with open(path, 'rb') as image_file:
        return f'data:{data_type};base64,' + \
            base64.b64encode(image_file.read()).decode('ascii')


def is_url(path):
    """
    Check if the path is a url or something else

    Args:
        path: path of the file
    """
    return isinstance(path, str) and re.match(r'^(http://|https://)', path.lower())


def format_json_dict(result):
    """
    Formats the dict part of a json return by a GraphQL query into a python object

    Args:
        result: result of a GraphQL query
    """
    for key, value in result.items():
        if key in ['jsonInterface', 'jsonMetadata', 'jsonResponse']:
            if (value == '' or value is None) \
                    and not (is_url(value) and key == 'jsonInterface'):
                result[key] = {}
            elif isinstance(value, str):
                try:
                    if is_url(value):
                        result[key] = requests.get(value).json()
                    else:
                        result[key] = loads(value)
                except Exception as exception:
                    raise ValueError(
                        'Json Metadata / json response /'
                        ' json interface should be valid jsons') from exception
        else:
            result[key] = format_json(value)
    return result


def format_json(result):
    """
    Formats the json return by a GraphQL query into a python object

    Args:
        result: result of a GraphQL query
    """
    if result is None:
        return result
    if isinstance(result, list):
        return [format_json(elem) for elem in result]
    if isinstance(result, dict):
        return format_json_dict(result)
    return result


def fragment_builder(fields, type_of_fields):
    """
    Builds a GraphQL fragment for a list of fields to query

    Args:
        fields
        type_of_fields
    """
    fragment = ''
    subfields = [field.split('.', 1) for field in fields if '.' in field]
    if subfields:
        for subquery in {subfield[0] for subfield in subfields}:
            type_of_fields_subquery = getattr(type_of_fields, subquery)
            try:
                if issubclass(type_of_fields_subquery, object):
                    fields_subquery = [subfield[1]
                                       for subfield in subfields if subfield[0] == subquery]
                    new_fragment = fragment_builder(
                        fields_subquery, type_of_fields_subquery)
                    fragment += f' {subquery}{{{new_fragment}}}'
            except ValueError:
                print(f'{subquery} must be a valid subquery field')
        fields = [field for field in fields if '.' not in field]
    for field in fields:
        try:
            getattr(type_of_fields, field)
        except ValueError:
            print(f'{field} must be an instance of {type_of_fields}')
        if isinstance(field, str):
            fragment += f' {field}'
        else:
            raise Exception('Please provide the fields to query as strings')
    return fragment


def deprecate(
        msg: Optional[str] = None,
        removed_in: Optional[str] = None,
        _type=DeprecationWarning):
    """
    Decorator factory that tag a deprecated function.
    - To deprecated the whole function, you can give a message at the decorator level.
    - For more sharp condition on the warning message, integrate this warning inside the function
    but still tag the function with this decorator, without giving a message argument

    Args:
        msg: string message that will be displayed whenever the function is called
        removed_in: string version in the format "Major.Minor"
            in which the deprecation element has to be removed
        type: DeprecationWarning by default
    """
    def decorator(func):
        if removed_in:
            if len(removed_in.split('.')) != 2:
                raise ValueError(
                    f'"removed_in" argument in deprecate wrapper of the function {func.__name__}'
                    'should have the format "Major.Minor"')
            func.removed_in = removed_in

        @ functools.wraps(func)
        def wrapper(*args, **kwargs):
            if msg:
                warnings.warn(msg, _type, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def format_metadata(metadata):
    """
    Formats metadata

    Args:
        metadata: a python object
    """
    if metadata is None:
        return metadata
    if isinstance(metadata, str):
        return metadata
    if isinstance(metadata, (dict, list)):
        return dumps(metadata)
    raise Exception(
        f'Metadata {metadata} of type {type(metadata)} must either be None,'
        ' a string a list or a dict.')


def convert_to_list_of_none(array, length):
    """
    Turns a value in a list of length length

    Args:
        array
        length
    """
    if isinstance(array, list):
        if len(array) != length:
            raise Exception(f'array should have length {length}')
        return array
    return [None] * length


def is_none_or_empty(_object):
    """
    Tests if an object is none or empty

    Args:
        object: a python object
    """
    object_is_empty = isinstance(_object, list) and len(_object) == 0
    return _object is None or object_is_empty


def list_is_not_none_else_none(_object):
    """
    Formats an object as a singleton if not none

    Args:
        object: a python object
    """
    return [_object] if _object is not None else None


def infer_id_from_external_id(kili, asset_id: str, external_id: str, project_id: str):
    """
    Infer asset id from external id

    Args:
        asset_id: asset id
        external_id: external id
        project_id: project id
    """
    if asset_id is None and external_id is None:
        raise Exception(
            'Either provide asset_id or external_id and project_id')
    if asset_id is not None:
        return asset_id
    assets = kili.assets(
        external_id_contains=[external_id], project_id=project_id, fields=['id'], disable_tqdm=True)
    if len(assets) == 0:
        raise Exception(
            f'No asset found with external ID "{external_id}"')
    if len(assets) > 1:
        raise Exception(
            f'Several assets found containing external ID "{external_id}":'
            f' {assets}. Please, use asset ID instead.')
    return assets[0]['id']


def validate_category_search_query(query):
    """Validate the category search query
    Args:
        query: the query to parse

    Raises:
        ValueError: if `query` is invalid
    """
    operator = pp.oneOf(">= <= > < ==")
    number = pp.pyparsing_common.number()
    dot = '.'
    word = pp.Word(pp.alphas, pp.alphanums + "_-*")
    identifier = word + dot + word + dot + 'count'
    condition = identifier + operator + number

    expr = pp.infixNotation(condition, [
        ("AND", 2, pp.opAssoc.LEFT, ),
        ("OR", 2, pp.opAssoc.LEFT, ),
    ])
    try:
        expr.parseString(query, parseAll=True)
    except pp.ParseException as error:
        raise ValueError(f'Invalid category search query: {query}') from error
