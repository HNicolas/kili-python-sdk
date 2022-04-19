
"""
Asset queries
"""

from json import dumps
from typing import Generator, List, Optional, Union
import warnings

from typeguard import typechecked
import pandas as pd

from ...helpers import Compatible, deprecate, format_result, fragment_builder
from .queries import gql_assets, GQL_ASSETS_COUNT
from ...types import Asset as AssetType
from ...orm import Asset
from ...utils import row_generator_from_paginated_calls


class QueriesAsset:
    """
    Set of Asset queries
    """
    # pylint: disable=too-many-arguments,too-many-locals

    def __init__(self, auth):
        """
        Initializes the subclass

        Parameters
        ----------
        - auth : KiliAuth object
        """
        self.auth = auth

    # pylint: disable=dangerous-default-value
    @Compatible(['v1', 'v2'])
    @typechecked
    def assets(self,
               asset_id: Optional[str] = None,
               project_id: Optional[str] = None,
               skip: int = 0,
               fields: list = ['content',
                               'createdAt',
                               'externalId',
                               'id',
                               'isHoneypot',
                               'jsonMetadata',
                               'labels.author.id',
                               'labels.author.email',
                               'labels.createdAt',
                               'labels.id',
                               'labels.jsonResponse',
                               'skipped',
                               'status'],
               asset_id_in: Optional[List[str]] = None,
               consensus_mark_gt: Optional[float] = None,
               consensus_mark_lt: Optional[float] = None,
               disable_tqdm: bool = False,
               external_id_contains: Optional[List[str]] = None,
               first: Optional[int] = None,
               format: Optional[str] = None,  # pylint: disable=redefined-builtin
               honeypot_mark_gt: Optional[float] = None,
               honeypot_mark_lt: Optional[float] = None,
               label_author_in: Optional[List[str]] = None,
               label_consensus_mark_gt: Optional[float] = None,
               label_consensus_mark_lt: Optional[float] = None,
               label_created_at: Optional[str] = None,
               label_created_at_gt: Optional[str] = None,
               label_created_at_lt: Optional[str] = None,
               label_honeypot_mark_gt: Optional[float] = None,
               label_honeypot_mark_lt: Optional[float] = None,
               label_json_response_contains: Optional[List[str]] = None,
               label_type_in: Optional[List[str]] = None,
               metadata_where: Optional[dict] = None,
               skipped: Optional[bool] = None,
               status_in: Optional[List[str]] = None,
               updated_at_gte: Optional[str] = None,
               updated_at_lte: Optional[str] = None,
               as_generator: bool = False,
               ) -> Union[List[dict], Generator[dict, None, None], pd.DataFrame]:
        # pylint: disable=line-too-long
        """
        Gets an asset list, an asset generator or a pandas DataFrame that match a set of constraints.

        Parameters
        ----------
        - asset_id : str, optional (default = None)
            The unique id of the asset to retrieve.
        - asset_id_in : list of str, optional (default = None)
            A list of the ids of the assets to retrieve.
        - project_id : str
            Identifier of the project.
        - skip : int, optional (default = None)
            Number of assets to skip (they are ordered by their date of creation, first to last).
        - fields : list of string, optional (default = ['id', 'content', 'externalId', 'isHoneypot',
            'isUsedForConsensus', 'jsonMetadata', 'labels.author.id', 'labels.author.email',
            'labels.jsonResponse', 'labels.skipped', 'priority', 'projects.id', 'projects.title',
            'project.jsonInterface'])
            All the fields to request among the possible fields for the assets.
            See [the documentation](https://cloud.kili-technology.com/docs/python-graphql-api/graphql-api/#asset) for all possible fields.
        - first : int, optional (default = None)
            Maximum number of assets to return.
        - consensus_mark_gt : float, optional (default = None)
            Minimum amount of consensus for the asset.
        - consensus_mark_lt : float, optional (default = None)
            Maximum amount of consensus for the asset.
        - external_id_contains : list of str, optional (default = None)
            Returned assets have an external id that belongs to that list, if given.
        - metadata_where : dict, optional (default = None)
            Filters by the values of the metadata of the asset.
            - metadata_where = {key1: "value1"} to filter on assets whose metadata
                have key "key1" with value "value1"
            - metadata_where = {key1: ["value1", "value2"]} to filter on assets whose metadata
                have key "key1" with value "value1" or value "value2
            - metadata_where = {key2: [2, 10]} to filter on assets whose metadata
                have key "key2" with a value between 2 and 10.
        - honeypot_mark_gt : float, optional (default = None)
            Minimum amount of honeypot for the asset.
        - honeypot_mark_lt : float, optional (default = None)
            Maximum amount of honeypot for the asset.
        - status_in : list of str, optional (default = None)
            Returned assets should have a status that belongs to that list, if given.
            Possible choices : {'TODO', 'ONGOING', 'LABELED', 'REVIEWED'}
        - label_type_in : list of str, optional (default = None)
            Returned assets should have a label whose type belongs to that list, if given.
        - label_author_in : list of str, optional (default = None)
            Returned assets should have a label whose status belongs to that list, if given.
        - label_consensus_mark_gt, optional (default = None)
            Returned assets should have a label whose consensus is greater than this number.
        - label_consensus_mark_lt : float, optional (default = None)
            Returned assets should have a label whose consensus is lower than this number.
        - label_created_at : string, optional (default = None)
            Returned assets should have a label whose creation date is equal to this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_created_at_gt : string, optional (default = None)
            Returned assets should have a label whose creation date is greater than this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_created_at_lt : string, optional (default = None)
            Returned assets should have a label whose creation date is lower than this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_json_response_contains : list of str, optional (default = None)
            Returned assets should have a substring of the label's jsonResponse
                that belongs to that list, if given.
        - label_honeypot_mark_gt : float, optional (default = None)
            Returned assets should have a label whose honeypot is greater than this number.
        - label_honeypot_mark_lt : float, optional (default = None)
            Returned assets should have a label whose honeypot is lower than this number.
        - skipped : bool, optional (default = None)
            Returned assets should be skipped
        - updated_at_gte : string, optional (default = None)
            Returned assets should have a label whose update date is greated or equal to this date.
            Formatted string should have format : "YYYY-MM-DD"
        - updated_at_lte : string, optional (default = None)
            Returned assets should have a label whose update date is lower or equal to this date.
            Formatted string should have format : "YYYY-MM-DD"
        - format : str, optional (default = None)
            If equal to 'pandas', returns a pandas DataFrame
        - disable_tqdm : bool, (default = False)
        - as_generator: bool, (default = False)
            If True, a generator on the assets is returned.

        Returns
        -------
        - a result object which contains the query if it was successful, else an error message.

        Examples
        -------
        >>> kili.assets(project_id=project_id) # returns the assets list of the project
        >>> kili.assets(asset_id=asset_id)
        >>> kili.assets(project_id=project_id, as_generator=True) # returns a generator of the project assets
        """
        if format == "pandas" and as_generator:
            raise ValueError(
                "Argument values as_generator==True and format==\"pandas\" are not compatible.")

        if as_generator is False:
            warnings.warn("From 2022-05-18, the default return type will be a generator. Currently, the default return type is a list. \n"
                          "If you want to force the query return to be a list, you can already call this method with the argument as_generator=False",
                          DeprecationWarning)

        saved_args = locals()
        count_args = {k: v for (k, v) in saved_args.items()
                      if k not in ['skip', 'first', 'disable_tqdm', 'format', 'fields', 'self', 'as_generator']}

        # using tqdm with a generator is messy, so it is always disabled
        disable_tqdm = disable_tqdm or as_generator

        payload_query = {
            'where': {
                'id': asset_id,
                'project': {
                    'id': project_id,
                },
                'externalIdIn': external_id_contains,
                'statusIn': status_in,
                'consensusMarkGte': consensus_mark_gt,
                'consensusMarkLte': consensus_mark_lt,
                'honeypotMarkGte': honeypot_mark_gt,
                'honeypotMarkLte': honeypot_mark_lt,
                'idIn': asset_id_in,
                'metadata': metadata_where,
                'label': {
                    'typeIn': label_type_in,
                    'authorIn': label_author_in,
                    'consensusMarkGte': label_consensus_mark_gt,
                    'consensusMarkLte': label_consensus_mark_lt,
                    'createdAt': label_created_at,
                    'createdAtGte': label_created_at_gt,
                    'createdAtLte': label_created_at_lt,
                    'honeypotMarkGte': label_honeypot_mark_gt,
                    'honeypotMarkLte': label_honeypot_mark_lt,
                    'jsonResponseContains': label_json_response_contains,
                },
                'skipped': skipped,
                'updatedAtGte': updated_at_gte,
                'updatedAtLte': updated_at_lte,
            },
        }

        asset_generator = row_generator_from_paginated_calls(
            skip,
            first,
            self.count_assets,
            count_args,
            self._query_assets,
            payload_query,
            fields,
            disable_tqdm
        )

        if format == "pandas":
            return pd.DataFrame(list(asset_generator))
        if as_generator:
            return asset_generator
        return list(asset_generator)

    def _query_assets(self,
                      skip: int,
                      first: int,
                      payload: dict,
                      fields: List[str]):

        payload.update({"skip": skip, "first": first})
        _gql_assets = gql_assets(fragment_builder(fields, AssetType))
        result = self.auth.client.execute(_gql_assets, payload)
        assets = format_result('data', result, Asset)
        return assets

    @Compatible(['v1', 'v2'])
    @typechecked
    def count_assets(self, asset_id: Optional[str] = None,
                     project_id: Optional[str] = None,
                     asset_id_in: Optional[List[str]] = None,
                     external_id_contains: Optional[List[str]] = None,
                     metadata_where: Optional[dict] = None,
                     status_in: Optional[List[str]] = None,
                     consensus_mark_gt: Optional[float] = None,
                     consensus_mark_lt: Optional[float] = None,
                     honeypot_mark_gt: Optional[float] = None,
                     honeypot_mark_lt: Optional[float] = None,
                     label_type_in: Optional[List[str]] = None,
                     label_author_in: Optional[List[str]] = None,
                     label_consensus_mark_gt: Optional[float] = None,
                     label_consensus_mark_lt: Optional[float] = None,
                     label_created_at: Optional[str] = None,
                     label_created_at_gt: Optional[str] = None,
                     label_created_at_lt: Optional[str] = None,
                     label_honeypot_mark_gt: Optional[float] = None,
                     label_honeypot_mark_lt: Optional[float] = None,
                     label_json_response_contains: Optional[List[str]] = None,
                     skipped: Optional[bool] = None,
                     updated_at_gte: Optional[str] = None,
                     updated_at_lte: Optional[str] = None):
        """
        Count and return the number of assets with the given constraints

        Parameters beginning with 'label_' apply to labels, others apply to assets.

        Parameters
        ----------
        - asset_id : str, optional (default = None)
            The unique id of the asset to retrieve.
        - asset_id_in : list of str, optional (default = None)
            A list of the ids of the assets to retrieve.
        - project_id : str, optional (default = None)
            Identifier of the project
        - external_id_contains : list of str, optional (default = None)
            Returned assets should have an external id that belongs to that list, if given.
        - metadata_where : dict, optional (default = None)
            Filters by the values of the metadata of the asset.
            - metadata_where = {key1: "value1"} to filter on assets whose metadata have key "key1"
                with value "value1"
            - metadata_where = {key1: ["value1", "value2"]} to filter on assets whose metadata
                have key "key1" with value "value1" or value "value2
            - metadata_where = {key2: [2, 10]} to filter on assets whose metadata have key "key2"
                with a value between 2 and 10.
        - status_in : list of str, optional (default = None)
            Returned assets should have a status that belongs to that list, if given.
            Possible choices : {'TODO', 'ONGOING', 'LABELED', 'REVIEWED'}
        - consensus_mark_gt : float, optional (default = None)
            Minimum amount of consensus for the asset.
        - consensus_mark_lt : float, optional (default = None)
            Maximum amount of consensus for the asset.
        - honeypot_mark_gt : float, optional (default = None)
            Minimum amount of honeypot for the asset.
        - honeypot_mark_lt : float, optional (default = None)
            Maximum amount of consensus for the asset.
        - label_type_in : list of str, optional (default = None)
            Returned assets should have a label whose type belongs to that list, if given.
        - label_author_in : list of str, optional (default = None)
            Returned assets should have a label whose status belongs to that list, if given.
        - label_consensus_mark_gt : float, optional (default = None)
            Returned assets should have a label whose consensus is greater than this number.
        - label_consensus_mark_lt : float, optional (default = None)
            Returned assets should have a label whose consensus is lower than this number.
        - label_created_at : string, optional (default = None)
            Returned assets should have a label whose creation date is equal to this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_created_at_gt : string, optional (default = None)
            Returned assets should have a label whose creation date is greater than this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_created_at_lt : string, optional (default = None)
            Returned assets should have a label whose creation date is lower than this date.
            Formatted string should have format : "YYYY-MM-DD"
        - label_honeypot_mark_gt : float, optional (default = None)
            Returned assets should have a label whose honeypot is greater than this number.
        - label_honeypot_mark_lt : float, optional (default = None)
            Returned assets should have a label whose honeypot is lower than this number.
        - label_json_response_contains : list of str, optional (default = None)
            Returned assets should have a substring of the label's jsonResponse that belongs
            to that list, if given.
        - skipped : bool, optional (default = None)
            Returned assets should be skipped
        - updated_at_gte : string, optional (default = None)
            Returned assets should have a label whose update date is greated or equal to this date.
            Formatted string should have format : "YYYY-MM-DD"
        - updated_at_lte : string, optional (default = None)
            Returned assets should have a label whose update date is lower or equal to this date.
            Formatted string should have format : "YYYY-MM-DD"

        Returns
        -------
        - a result object which contains the query if it was successful, or an error message else.

        Examples
        -------
        >>> kili.count_assets(project_id=project_id)
        250
        >>> kili.count_assets(asset_id=asset_id)
        1
        """
        variables = {
            'where': {
                'id': asset_id,
                'project': {
                    'id': project_id,
                },
                'externalIdIn': external_id_contains,
                'statusIn': status_in,
                'consensusMarkGte': consensus_mark_gt,
                'consensusMarkLte': consensus_mark_lt,
                'honeypotMarkGte': honeypot_mark_gt,
                'honeypotMarkLte': honeypot_mark_lt,
                'idIn': asset_id_in,
                'metadata': metadata_where,
                'label': {
                    'typeIn': label_type_in,
                    'authorIn': label_author_in,
                    'consensusMarkGte': label_consensus_mark_gt,
                    'consensusMarkLte': label_consensus_mark_lt,
                    'createdAt': label_created_at,
                    'createdAtGte': label_created_at_gt,
                    'createdAtLte': label_created_at_lt,
                    'honeypotMarkGte': label_honeypot_mark_gt,
                    'honeypotMarkLte': label_honeypot_mark_lt,
                    'jsonResponseContains': label_json_response_contains,
                },
                'skipped': skipped,
                'updatedAtGte': updated_at_gte,
                'updatedAtLte': updated_at_lte,
            }
        }
        result = self.auth.client.execute(GQL_ASSETS_COUNT, variables)
        count = format_result('data', result)
        return count
