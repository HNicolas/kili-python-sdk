from .fragments import AUTH_PAYLOAD_FRAGMENT, USER_FRAGMENT

GQL_SIGN_IN = f'''
mutation($email: String!, $password: String!) {{
  data: signIn(email: $email password: $password) {{
    {AUTH_PAYLOAD_FRAGMENT}
  }}
}}
'''

GQL_CREATE_USER = f'''
mutation(
    $name: String!
    $email: String!
    $password: String!
    $organizationRole: OrganizationRole!
) {{
  data: createUser(name: $name
      email: $email
      password: $password
      organizationRole: $organizationRole) {{
    {USER_FRAGMENT}
  }}
}}
'''

GQL_CREATE_USER_FROM_EMAIL_IF_NOT_EXISTS = f'''
mutation(
    $name: String!
    $email: String!
    $organizationRole: OrganizationRole!
    $projectID: String!
) {{
  data: createUserFromEmailIfNotExists(name: $name
      email: $email
      organizationRole: $organizationRole
      projectID: $projectID) {{
    {USER_FRAGMENT}
  }}
}}
'''

GQL_UPDATE_API_KEY = f'''
mutation(
    $newApiKey: String!
    $where: UserWhere!
) {{
  data: updateApiKey(
    newApiKey: $newApiKey
    where: $where
  ) {{
    {USER_FRAGMENT}
  }}
}}
'''

GQL_UPDATE_PASSWORD = f'''
mutation(
    $oldPassword: String!
    $newPassword1: String!
    $newPassword2: String!
    $where: UserWhere!
) {{
  data: updatePassword(
    oldPassword: $oldPassword
    newPassword1: $newPassword1
    newPassword2: $newPassword2
    where: $where
  ) {{
    {USER_FRAGMENT}
  }}
}}
'''

GQL_RESET_PASSWORD = f'''
mutation($where: UserWhere!) {{
  data: resetPassword(where: $where) {{
    {USER_FRAGMENT}
  }}
}}
'''

GQL_UPDATE_PROPERTIES_IN_USER = f'''
mutation(
    $email: String!
    $name: String
    $organizationId: String
    $organizationRole: OrganizationRole
    $activated: Boolean
) {{
  data: updatePropertiesInUser(
    where: {{email: $email}}
    data: {{
      name: $name
      email: $email
      organizationId: $organizationId
      organizationRole: $organizationRole
      activated: $activated
    }}
  ) {{
    {USER_FRAGMENT}
  }}
}}
'''
