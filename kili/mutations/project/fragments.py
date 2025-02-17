"""
Fragments of project mutations
"""

PROJECT_FRAGMENT = '''
id
jsonInterface
title
roles {
    user {
      id
      email
    }
    role
}
'''

PROJECT_FRAGMENT_ID = '''
id
'''

PROJECT_FRAGMENT_PUBLIC_TOKEN = '''
id
publicToken
'''

ROLE_FRAGMENT = '''
user {
  id
  email
}
role
'''
