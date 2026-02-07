# API Contracts: Core Projects MVP

**Phase**: 1 (Design & Contracts)
**Date**: January 14, 2026
**Purpose**: Define REST API endpoints, request/response formats, and error handling

## Base URL

```
/api/v1/projects/
```

---

## Endpoints

### List Projects

**Endpoint**: `GET /api/v1/projects/`

**Description**: Retrieve paginated list of projects with filtering

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Results per page (default: 50, max: 100) |
| search | string | No | Search in name and descriptions |
| status | integer | No | Filter by status |
| visibility | integer | No | Filter by visibility |
| owner | integer | No | Filter by owner organization ID |
| keywords | string | No | Comma-separated keyword IDs |
| tags | string | No | Comma-separated tag names |
| ordering | string | No | Sort field (name, -name, modified, -modified) |

**Request Example**:

```http
GET /api/v1/projects/?status=2&visibility=2&page=1&page_size=20
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "count": 150,
  "next": "https://example.com/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "uuid": "p_AB12CD34",
      "name": "Arctic Climate Study 2024-2026",
      "status": 2,
      "status_display": "Active",
      "visibility": 2,
      "visibility_display": "Public",
      "owner": {
        "id": 45,
        "name": "Geological Survey Laboratory",
        "url": "https://example.com/api/v1/organizations/45/"
      },
      "image": "https://example.com/media/projects/arctic_study.jpg",
      "keywords": [
        {
          "id": 10,
          "label": "Climate Change",
          "uri": "https://vocab.example.org/climate-change"
        }
      ],
      "added": "2024-01-15T10:30:00Z",
      "modified": "2024-06-20T14:22:00Z",
      "url": "https://example.com/api/v1/projects/123/"
    }
  ]
}
```

**Permissions**:

- Authenticated users: See all projects they have view permission for
- Anonymous users: See only public projects

---

### Retrieve Project

**Endpoint**: `GET /api/v1/projects/{id}/`

**Description**: Retrieve detailed project information

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Project ID |

**Request Example**:

```http
GET /api/v1/projects/123/
Authorization: Bearer <token>
```

**Response** (200 OK):

```json
{
  "id": 123,
  "uuid": "p_AB12CD34",
  "name": "Arctic Climate Study 2024-2026",
  "status": 2,
  "status_display": "Active",
  "visibility": 2,
  "visibility_display": "Public",
  "owner": {
    "id": 45,
    "name": "Geological Survey Laboratory",
    "short_name": "GSL",
    "url": "https://example.com/api/v1/organizations/45/"
  },
  "image": "https://example.com/media/projects/arctic_study.jpg",
  "funding": [
    {
      "funderName": "National Science Foundation",
      "funderIdentifier": "https://ror.org/021nxhr62",
      "funderIdentifierType": "ROR",
      "awardNumber": "1234567",
      "awardURI": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=1234567",
      "awardTitle": "Understanding Arctic Climate Change"
    }
  ],
  "descriptions": [
    {
      "id": 1001,
      "type": "Abstract",
      "text": "This project investigates the impact of climate change on Arctic ice sheets...",
      "order": 0
    },
    {
      "id": 1002,
      "type": "Methods",
      "text": "We employ satellite imagery analysis combined with field measurements...",
      "order": 1
    }
  ],
  "dates": [
    {
      "id": 2001,
      "type": "Project Start",
      "date": "2024-01-15",
      "end_date": null,
      "order": 0
    },
    {
      "id": 2002,
      "type": "Project End",
      "date": "2026-12-31",
      "end_date": null,
      "order": 1
    }
  ],
  "identifiers": [
    {
      "id": 3001,
      "type": "DOI",
      "identifier": "10.5555/example.doi",
      "url": "https://doi.org/10.5555/example.doi",
      "order": 0
    },
    {
      "id": 3002,
      "type": "Grant Number",
      "identifier": "NSF-1234567",
      "url": null,
      "order": 1
    }
  ],
  "contributors": [
    {
      "id": 4001,
      "contributor": {
        "id": 100,
        "name": "Dr. Jane Smith",
        "orcid": "0000-0001-2345-6789",
        "url": "https://example.com/api/v1/persons/100/"
      },
      "role": "Principal Investigator"
    }
  ],
  "keywords": [
    {
      "id": 10,
      "label": "Climate Change",
      "uri": "https://vocab.example.org/climate-change"
    },
    {
      "id": 11,
      "label": "Arctic Research",
      "uri": "https://vocab.example.org/arctic-research"
    }
  ],
  "tags": ["ice-core", "temperature", "sea-level"],
  "dataset_count": 12,
  "added": "2024-01-15T10:30:00Z",
  "modified": "2024-06-20T14:22:00Z",
  "url": "https://example.com/api/v1/projects/123/"
}
```

**Error Responses**:

- 404 Not Found: Project does not exist
- 403 Forbidden: User does not have view permission

---

### Create Project

**Endpoint**: `POST /api/v1/projects/`

**Description**: Create a new project (streamlined)

**Request Body**:

```json
{
  "name": "Arctic Climate Study 2024-2026",
  "status": 0,
  "visibility": 0,
  "owner": 45
}
```

**Request Example**:

```http
POST /api/v1/projects/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Arctic Climate Study 2024-2026",
  "status": 0,
  "visibility": 0,
  "owner": 45
}
```

**Response** (201 Created):

```json
{
  "id": 124,
  "uuid": "p_XY98ZW76",
  "name": "Arctic Climate Study 2024-2026",
  "status": 0,
  "status_display": "Concept",
  "visibility": 0,
  "visibility_display": "Private",
  "owner": {
    "id": 45,
    "name": "Geological Survey Laboratory",
    "url": "https://example.com/api/v1/organizations/45/"
  },
  "image": null,
  "keywords": [],
  "added": "2024-06-21T09:15:00Z",
  "modified": "2024-06-21T09:15:00Z",
  "url": "https://example.com/api/v1/projects/124/"
}
```

**Validation Errors** (400 Bad Request):

```json
{
  "name": ["This field is required."],
  "status": ["This field is required."],
  "visibility": ["This field is required."]
}
```

**Permissions**:

- Authenticated users with project creation permission

---

### Update Project

**Endpoint**: `PATCH /api/v1/projects/{id}/` or `PUT /api/v1/projects/{id}/`

**Description**: Update project metadata

**Request Body** (PATCH - partial update):

```json
{
  "name": "Arctic Climate Study 2024-2027 (Extended)",
  "status": 2,
  "visibility": 2
}
```

**Request Example**:

```http
PATCH /api/v1/projects/123/
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": 2,
  "visibility": 2
}
```

**Response** (200 OK):

```json
{
  "id": 123,
  "uuid": "p_AB12CD34",
  "name": "Arctic Climate Study 2024-2027 (Extended)",
  "status": 2,
  "status_display": "Active",
  "visibility": 2,
  "visibility_display": "Public",
  ...
}
```

**Validation Errors** (400 Bad Request):

```json
{
  "visibility": ["Projects in Concept phase cannot be made public."]
}
```

**Permissions**:

- Users with change_project_metadata or change_project_settings permission
- Role-based field restrictions enforced

**Error Responses**:

- 404 Not Found: Project does not exist
- 403 Forbidden: User does not have edit permission

---

### Delete Project

**Endpoint**: `DELETE /api/v1/projects/{id}/`

**Description**: Delete a project

**Request Example**:

```http
DELETE /api/v1/projects/123/
Authorization: Bearer <token>
```

**Response** (204 No Content): (empty body)

**Validation Errors** (400 Bad Request):

```json
{
  "detail": "Cannot delete project with associated datasets. Delete datasets first or use force=true."
}
```

**Permissions**:

- Users with delete_project permission (typically only owner)

**Error Responses**:

- 404 Not Found: Project does not exist
- 403 Forbidden: User does not have delete permission
- 400 Bad Request: Project has datasets (soft protection)

---

### Add Description

**Endpoint**: `POST /api/v1/projects/{id}/descriptions/`

**Description**: Add a description to a project

**Request Body**:

```json
{
  "type": "Abstract",
  "text": "This project investigates the impact of climate change on Arctic ice sheets..."
}
```

**Response** (201 Created):

```json
{
  "id": 1003,
  "type": "Abstract",
  "text": "This project investigates the impact of climate change on Arctic ice sheets...",
  "order": 0,
  "added": "2024-06-21T10:00:00Z",
  "modified": "2024-06-21T10:00:00Z"
}
```

**Validation Errors** (400 Bad Request):

```json
{
  "type": ["A description of this type already exists for this project."]
}
```

---

### Update Description

**Endpoint**: `PATCH /api/v1/projects/{id}/descriptions/{desc_id}/`

**Request Body**:

```json
{
  "text": "Updated abstract text...",
  "order": 1
}
```

**Response** (200 OK):

```json
{
  "id": 1003,
  "type": "Abstract",
  "text": "Updated abstract text...",
  "order": 1,
  "modified": "2024-06-21T11:30:00Z"
}
```

---

### Delete Description

**Endpoint**: `DELETE /api/v1/projects/{id}/descriptions/{desc_id}/`

**Response** (204 No Content)

---

## Similar Endpoints for Dates and Identifiers

- `POST /api/v1/projects/{id}/dates/`
- `PATCH /api/v1/projects/{id}/dates/{date_id}/`
- `DELETE /api/v1/projects/{id}/dates/{date_id}/`
- `POST /api/v1/projects/{id}/identifiers/`
- `PATCH /api/v1/projects/{id}/identifiers/{id_id}/`
- `DELETE /api/v1/projects/{id}/identifiers/{id_id}/`

---

## Metadata Export Endpoints

### DataCite JSON

**Endpoint**: `GET /api/v1/projects/{id}/export/datacite/`

**Response** (200 OK):

```json
{
  "data": {
    "type": "dois",
    "attributes": {
      "prefix": "10.5555",
      "suffix": "example.project",
      "identifiers": [
        {
          "identifier": "https://doi.org/10.5555/example.project",
          "identifierType": "DOI"
        }
      ],
      "creators": [
        {
          "name": "Smith, Jane",
          "nameType": "Personal",
          "givenName": "Jane",
          "familyName": "Smith",
          "nameIdentifiers": [
            {
              "nameIdentifier": "https://orcid.org/0000-0001-2345-6789",
              "nameIdentifierScheme": "ORCID",
              "schemeUri": "https://orcid.org"
            }
          ]
        }
      ],
      "titles": [
        {
          "title": "Arctic Climate Study 2024-2026"
        }
      ],
      "publisher": "Geological Survey Laboratory",
      "publicationYear": "2024",
      "resourceType": {
        "resourceTypeGeneral": "Dataset",
        "resourceType": "Research Project"
      },
      "descriptions": [
        {
          "description": "This project investigates the impact of climate change on Arctic ice sheets...",
          "descriptionType": "Abstract"
        },
        {
          "description": "We employ satellite imagery analysis...",
          "descriptionType": "Methods"
        }
      ],
      "fundingReferences": [
        {
          "funderName": "National Science Foundation",
          "funderIdentifier": "https://ror.org/021nxhr62",
          "funderIdentifierType": "ROR",
          "awardNumber": "1234567",
          "awardURI": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=1234567",
          "awardTitle": "Understanding Arctic Climate Change"
        }
      ]
    }
  }
}
```

---

### JSON-LD

**Endpoint**: `GET /api/v1/projects/{id}/export/jsonld/`

**Response** (200 OK):

```json
{
  "@context": "https://schema.org",
  "@type": "ResearchProject",
  "@id": "https://example.com/projects/p_AB12CD34",
  "name": "Arctic Climate Study 2024-2026",
  "description": "This project investigates the impact of climate change on Arctic ice sheets...",
  "identifier": "p_AB12CD34",
  "url": "https://example.com/projects/p_AB12CD34",
  "dateCreated": "2024-01-15T10:30:00Z",
  "dateModified": "2024-06-20T14:22:00Z",
  "keywords": ["Climate Change", "Arctic Research"],
  "funder": {
    "@type": "Organization",
    "name": "National Science Foundation",
    "identifier": "https://ror.org/021nxhr62"
  },
  "funding": {
    "@type": "Grant",
    "identifier": "NSF-1234567",
    "name": "Understanding Arctic Climate Change"
  },
  "contributor": [
    {
      "@type": "Person",
      "name": "Dr. Jane Smith",
      "identifier": "https://orcid.org/0000-0001-2345-6789",
      "roleName": "Principal Investigator"
    }
  ]
}
```

---

## Serializer Definitions

### ProjectListSerializer

**Fields**: id, uuid, name, status, status_display, visibility, visibility_display, owner (nested), image, keywords (nested), added, modified, url

**Read-Only**: id, uuid, status_display, visibility_display, added, modified, url

---

### ProjectDetailSerializer

**Fields**: All fields from ProjectListSerializer plus:

- funding (JSON)
- descriptions (nested)
- dates (nested)
- identifiers (nested)
- contributors (nested)
- tags
- dataset_count (computed)

**Nested Serializers**:

- ProjectDescriptionSerializer
- ProjectDateSerializer
- ProjectIdentifierSerializer
- ContributorSerializer (from contributors app)
- KeywordSerializer (from vocabularies app)

---

### ProjectCreateSerializer

**Fields**: name, status, visibility, owner

**Write-Only**: All fields (no read-only)

---

### ProjectUpdateSerializer

**Fields**: name, image, status, visibility, owner, funding, keywords, tags

**Read-Only**: None (all writable)

**Validation**:

- Enforces role-based field restrictions based on user permissions
- Validates DataCite funding schema if provided
- Prevents public visibility if status is Concept

---

## Error Response Format

**Standard Error Response**:

```json
{
  "detail": "Error message",
  "field_errors": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

**HTTP Status Codes**:

- 200 OK: Successful GET/PATCH/PUT
- 201 Created: Successful POST
- 204 No Content: Successful DELETE
- 400 Bad Request: Validation errors
- 401 Unauthorized: Missing authentication
- 403 Forbidden: Permission denied
- 404 Not Found: Resource not found
- 500 Internal Server Error: Server error

---

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Admin users: No limit

---

## Summary

- 8 primary endpoints: List, Retrieve, Create, Update, Delete, plus nested resource endpoints
- 2 export endpoints: DataCite JSON, JSON-LD
- Role-based permission enforcement
- Comprehensive validation with detailed error messages
- Nested serializers for related metadata
- Optimized queries with select_related/prefetch_related
- Standard REST conventions

Ready for quickstart guide generation.
