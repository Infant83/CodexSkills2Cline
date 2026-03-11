# OpenProject API patterns

Use this file when the default helper commands are not enough and a raw
`request` call needs custom query filters or JSON payloads.

## Filters

OpenProject collection filters are JSON arrays encoded into the `filters`
query parameter.

Search users by login, name, or email:

```json
[
  {
    "name_and_email_or_login": {
      "operator": "**",
      "values": ["user@example.com"]
    }
  }
]
```

Filter work packages by project:

```json
[
  {
    "project": {
      "operator": "=",
      "values": ["1"]
    }
  }
]
```

Filter work packages assigned to a user:

```json
[
  {
    "assignee": {
      "operator": "=",
      "values": ["5"]
    }
  }
]
```

Filter open work packages:

```json
[
  {
    "status": {
      "operator": "o",
      "values": [""]
    }
  }
]
```

## Create payloads

Minimal work package create payload:

```json
{
  "subject": "Prepare release notes",
  "_links": {
    "type": {
      "href": "/api/v3/types/1"
    }
  }
}
```

Add optional fields only after reading the project and type context:

```json
{
  "subject": "Prepare release notes",
  "description": {
    "format": "markdown",
    "raw": "Draft notes for the next release."
  },
  "_links": {
    "type": {
      "href": "/api/v3/types/1"
    },
    "assignee": {
      "href": "/api/v3/users/5"
    },
    "parent": {
      "href": "/api/v3/work_packages/2"
    }
  }
}
```

## Update payloads

Fetch the current resource first and copy its `lockVersion` into the patch:

```json
{
  "lockVersion": 1,
  "subject": "Updated subject"
}
```

Patch link fields by sending `_links` entries:

```json
{
  "lockVersion": 1,
  "_links": {
    "status": {
      "href": "/api/v3/statuses/7"
    },
    "assignee": {
      "href": "/api/v3/users/5"
    }
  }
}
```
