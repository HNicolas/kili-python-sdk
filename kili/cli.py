"""Kili CLI"""

from typing import Optional, Tuple
import click
from typeguard import typechecked
import pandas as pd
from tabulate import tabulate
from kili.client import Kili
from kili import __version__
from kili.exceptions import NotFound
from kili.mutations.asset.helpers import generate_json_metadata_array, get_file_paths_to_upload

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
def cli():
    """Kili Command line interface."""


@cli.group(context_settings=CONTEXT_SETTINGS)
def project():
    """Commands to interact with a Kili project"""


@project.command(name="list")
@click.option('--api-key', type=str, envvar='KILI_API_KEY', required=True,
              help='Your Api Key')
@click.option('--endpoint', type=str,
              default='https://cloud.kili-technology.com/api/label/v2/graphql',
              help='The API Endpoint')
@click.option('--max', 'first', type=int, help='Maximum number of project to display', default=100)
@click.option('--format', 'tablefmt', type=str, default='simple',
              help='Defines how the table is formatted (see tabulate format).')
def list_project(api_key: str,
                 endpoint: str,
                 tablefmt: str,
                 first: int):
    """
    List your projects

    Example:
        $ kili project list --max 10 --format pretty
    """
    kili = Kili(api_key=api_key, api_endpoint=endpoint)
    projects = kili.projects(fields=['title', 'id', 'description', 'numberOfAssets',
                             'numberOfRemainingAssets', 'numberOfReviewedAssets'], first=first)
    projects = pd.DataFrame(projects)
    projects['progress'] = round(
        (1 - projects['numberOfRemainingAssets'] / projects['numberOfAssets']) * 100, 1)
    projects = projects[['title', 'id', 'progress', 'description']]
    # Add '%' to progress if progress is not nan
    projects['progress'] = [(str(progress) + '%') if progress >=
                            0 else progress for progress in projects['progress']]
    # If description or title has more than 50 characters, truncate after 47 and add '...'
    projects['description'] = [(description[:47] + '...') if len(description)
                               > 50 else description for description in projects['description']]
    projects['title'] = [(title[:47] + '...') if len(title) >
                         50 else title for title in projects['title']]
    print(tabulate(projects, headers='keys', tablefmt=tablefmt,
          showindex=False, colalign=("left", "left", "right", "left")))


@project.command(name='import')
@click.argument('files', type=click.Path(), nargs=-1, required=True)
@click.option('--api-key', type=str, envvar='KILI_API_KEY', required=True,
              help='Your Api Key')
@click.option('--endpoint', type=str,
              default='https://cloud.kili-technology.com/api/label/v2/graphql',
              help='The API Endpoint')
@click.option('--project-id', type=str, required=True,
              help='Id of the project to import assets in')
@click.option('--exclude', type=click.Path(exists=True), multiple=True,
              help="Files to exclude from the given files")
@click.option('--frames', type=bool, default=False, is_flag=True,
              help="Only for a frame project, import videos as frames. "
              "The import time is longer with this option")
@click.option('--fps', type=int,
              help="Only for a frame project, import videos with a specific frame rate")
@typechecked
#pylint: disable=too-many-arguments
def import_assets(api_key: str,
                  endpoint: str,
                  project_id: str,
                  files: Tuple[str, ...],
                  exclude: Optional[Tuple[str, ...]],
                  fps: Optional[int],
                  frames: bool):
    """
    Add assets into a project.

    Files can be paths to files or to folders. You can provide several paths separated by spaces.

    Examples:
        $ kili project import --project-id <project_id> dir1/dir2/ dir1/dir3/test1.png
        --exclude dontimport.png

        $ kili project import --project-id <project_id> dir1/dir3/video.mp4 --frames --fps 24


    Currently, this command does not support:

        - the import of videos from local frames, rich text and time series assets

        - the import of assets with metadata or with a custom external_id

    For such imports, please use the `append_many_to_dataset` method in the Kili SDK.
    """
    kili = Kili(api_key=api_key, api_endpoint=endpoint)
    try:
        input_type = kili.projects(project_id,
                                   disable_tqdm=True,
                                   fields=['inputType'])[0]['inputType']
    except:
        # pylint: disable=raise-missing-from
        raise NotFound(f'project ID: {project_id}')

    if input_type != 'FRAME' and (fps is not None or frames is True):
        illegal_option = 'fps and frames are'
        if frames is False:
            illegal_option = 'fps is'
        if fps is None:
            illegal_option = 'frames is'
        raise ValueError(f'{illegal_option} only valid for a FRAME project')

    files_to_upload = get_file_paths_to_upload(files, input_type, exclude)
    if len(files_to_upload) == 0:
        raise ValueError(
            'No files to upload. '
            'Check that the paths exist and that the file types are compatible with the project')
    external_ids = [path.split('/')[-1] for path in files_to_upload]
    json_metadata_array = generate_json_metadata_array(
        frames, fps, len(files_to_upload), input_type)

    kili.append_many_to_dataset(
        project_id=project_id,
        content_array=files_to_upload,
        external_id_array=external_ids,
        json_metadata_array=json_metadata_array)

    print(f'\n{len(files_to_upload)} files have been successfully imported')


def main() -> None:
    """Execute the main function of the command line."""
    cli()


if __name__ == "__main__":
    main()
