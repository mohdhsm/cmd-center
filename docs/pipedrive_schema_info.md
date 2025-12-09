# This includes pipdrive schema to be used and references

## Activity Return json from the api call for one activity

api call :

```text
https://gyptech.postman.co/workspace/My-Workspace~5bac1145-c160-4f7c-85b8-86c686689cad/example/15377930-74870a62-55ae-46d7-aa38-edd4b8442e77?action=share&creator=15377930
```

```json
{
  "success": true,
  "data": {
    "id": 1,
    "subject": "Activity Subject",
    "type": "activity_type",
    "owner_id": 1,
    "creator_user_id": 1,
    "is_deleted": false,
    "add_time": "2021-01-01T00:00:00Z",
    "update_time": "2021-01-01T00:00:00Z",
    "deal_id": 5,
    "lead_id": "abc-def",
    "person_id": 6,
    "org_id": 7,
    "project_id": 8,
    "due_date": "2021-01-01",
    "due_time": "15:00:00",
    "duration": "01:00:00",
    "busy": true,
    "done": true,
    "marked_as_done_time": "2021-01-01T00:00:00Z",
    "location": {
      "value": "123 Main St",
      "country": "USA",
      "admin_area_level_1": "CA",
      "admin_area_level_2": "Santa Clara",
      "locality": "Sunnyvale",
      "sublocality": "Downtown",
      "route": "Main St",
      "street_number": "123",
      "postal_code": "94085"
    },
    "participants": [
      {
        "person_id": 1,
        "primary": true
      }
    ],
    "attendees": [
      {
        "email": "some@email.com",
        "name": "Some Name",
        "status": "accepted",
        "is_organizer": true,
        "person_id": 1,
        "user_id": 1
      }
    ],
    "conference_meeting_client": "google_meet",
    "conference_meeting_url": "https://meet.google.com/abc-xyz",
    "conference_meeting_id": "abc-xyz",
    "public_description": "Public Description",
    "priority": 263,
    "note": "Note"
  }
