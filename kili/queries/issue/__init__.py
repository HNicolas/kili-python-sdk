"""
Issue queries
"""

from dataclasses import dataclass
from typing import Generator, List, Optional, Union
import warnings

from typeguard import typechecked

from ...helpers import Compatible, format_result, fragment_builder
from .queries import GQL_ISSUES_COUNT, gql_issues
from ...types import Issue as IssueType
from ...utils import row_generator_from_paginated_calls


@dataclass
class QueriesIssue:
    """
    Set of Issue queries
    """
    # pylint: disable=too-many-arguments,too-many-locals

    def __init__(self, auth):
        """
        Initializes the subclass

        Parameters
        ----------
        auth : KiliAuth object
        """
        self.auth = auth

    # pylint: disable=dangerous-default-value
    @Compatible(['v1', 'v2'])
    @typechecked
    def issues(self,
               fields: Optional[List[str]] = [
                   'id',
                   'createdAt',
                   'hasBeenSeen',
                   'issueNumber',
                   'status',
                   'type'],
               first: Optional[int] = 100,
               project_id: Optional[str] = None,
               skip: Optional[int] = 0,
               disable_tqdm: bool = False,
               as_generator: bool = False) -> Union[List[dict], Generator[dict, None, None]]:
        # pylint: disable=line-too-long
        """
        Gets a generator or a list of issues that match a set of criteria

        Parameters
        ----------
        fields :
            All the fields to request among the possible fields for the assets.
            See [the documentation](https://cloud.kili-technology.com/docs/python-graphql-api/graphql-api/#issue) for all possible fields.
        first :
            Maximum number of issues to return.
        project_id :
            Project ID the issue belongs to.
        skip :
            Number of issues to skip (they are ordered by their date of creation, first to last).
        disable_tqdm :
            If True, the progress bar will be disabled
        as_generator:
            If True, a generator on the issues is returned.

        Returns
        -------
        dict
            a result object which contains the query if it was successful, or an error message else.

        Examples
        --------
        ```
        # List all issues of a project and their authors
        >>> kili.issues(project_id=project_id, fields=['author.email'])
        ```
        """

        count_args = {'project_id': project_id}
        disable_tqdm = disable_tqdm or as_generator
        payload_query = {
            'where': {
                'project': {
                    'id': project_id,
                },
            },
        }

        issues_generator = row_generator_from_paginated_calls(
            skip,
            first,
            self.count_issues,
            count_args,
            self._query_issues,
            payload_query,
            fields,
            disable_tqdm
        )

        if as_generator:
            return issues_generator
        return list(issues_generator)

    def _query_issues(self,
                      skip: int,
                      first: int,
                      payload: dict,
                      fields: List[str]):
        payload.update({'skip': skip, 'first': first})
        _gql_issues = gql_issues(fragment_builder(fields, IssueType))
        result = self.auth.client.execute(_gql_issues, payload)
        return format_result('data', result)

    @Compatible(['v2'])
    @typechecked
    def count_issues(self, project_id: Optional[str] = None) -> int:
        """
        Count and return the number of api keys with the given constraints

        Parameters
        ----------
        project_id :
            Project ID the issue belongs to.

        Returns
        -------
        dict
            the number of issues with the parameters provided

        """
        variables = {
            'where': {
                'project': {
                    'id': project_id,
                },
            },
        }
        result = self.auth.client.execute(GQL_ISSUES_COUNT, variables)
        count = format_result('data', result)
        return count
