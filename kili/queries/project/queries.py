"""
Queries of project queries
"""


def gql_projects(fragment: str):
    """
    Return the GraphQL projects query
    """
    return f'''
query($where: ProjectWhere!, $first: PageSize!, $skip: Int!) {{
  data: projects(where: $where, first: $first, skip: $skip) {{
    {fragment}
  }}
}}
'''


GQL_PROJECTS_COUNT = '''
query($where: ProjectWhere!) {
  data: countProjects(where: $where)
}
'''


GQL_PROJECT_EXPORT_DATA = f'''
query(
    $where: ProjectWhere!
    $exportType: ExportType
    $labelFormat: LabelFormat
    $versionName: String) {{
  data: exportData(
      where: $where
      exportType: $exportType
      labelFormat: $labelFormat
      versionName: $versionName
    )
}}
'''
