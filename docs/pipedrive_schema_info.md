# This includes pipdrive schema to be used and references

Mostly it will include the ID's of the stages, and custome fields, aswell as the return format of the json. Use the return json format for extracting the informatino that you need. 

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
  ```

# Deals Fields information

These are the deal fields, and the most important part are thier id.

```json
{
    "success": true,
    "data": [
        {
            "id": 12474,
            "key": "id",
            "name": "ID",
            "group_id": null,
            "order_nr": 0,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12451,
            "key": "title",
            "name": "Title",
            "group_id": null,
            "order_nr": 0,
            "field_type": "varchar",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 0,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "use_field": "id",
            "link": "/deal/"
        },
        {
            "id": 12452,
            "key": "creator_user_id",
            "name": "Creator",
            "group_id": null,
            "order_nr": 0,
            "field_type": "user",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12453,
            "key": "user_id",
            "name": "Owner",
            "group_id": null,
            "order_nr": 0,
            "field_type": "user",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 0,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12455,
            "key": "weighted_value",
            "name": "Weighted value",
            "group_id": null,
            "order_nr": 0,
            "field_type": "monetary",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": false,
            "sortable_flag": false,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": null,
            "key": "weighted_value_currency",
            "name": "Currency of Weighted value",
            "field_type": "varchar",
            "edit_flag": false,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": true,
            "parent_id": 12455,
            "id_suffix": "currency"
        },
        {
            "id": 12458,
            "key": "pipeline",
            "name": "Pipeline",
            "group_id": null,
            "order_nr": 0,
            "field_type": "double",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 0,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12460,
            "key": "stage_id",
            "name": "Stage",
            "group_id": null,
            "order_nr": 0,
            "field_type": "stage",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 0,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "use_field": "stage"
        },
        {
            "id": 12461,
            "key": "status",
            "name": "Status",
            "group_id": null,
            "order_nr": 0,
            "field_type": "status",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": "open",
                    "label": "Open"
                },
                {
                    "id": "lost",
                    "label": "Lost"
                },
                {
                    "id": "won",
                    "label": "Won"
                },
                {
                    "id": "deleted",
                    "label": "Deleted"
                }
            ]
        },
        {
            "id": 12462,
            "key": "add_time",
            "name": "Deal created",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12463,
            "key": "update_time",
            "name": "Update time",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12464,
            "key": "stage_change_time",
            "name": "Last stage change",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12465,
            "key": "next_activity_date",
            "name": "Next activity date",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12466,
            "key": "last_activity_date",
            "name": "Last activity date",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12467,
            "key": "won_time",
            "name": "Won time",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": {
                "status": "=won"
            },
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": true,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12468,
            "key": "last_incoming_mail_time",
            "name": "Last email received",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12469,
            "key": "last_outgoing_mail_time",
            "name": "Last email sent",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12470,
            "key": "lost_time",
            "name": "Lost time",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": {
                "status": "=lost"
            },
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12471,
            "key": "close_time",
            "name": "Deal closed on",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12472,
            "key": "lost_reason",
            "name": "Lost reason",
            "group_id": null,
            "order_nr": 0,
            "field_type": "varchar_options",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 15733715,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": {
                "status": "=lost"
            },
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            },
            "options": [
                {
                    "id": 49,
                    "label": "High Price"
                },
                {
                    "id": 50,
                    "label": "Long Lead Time"
                },
                {
                    "id": 51,
                    "label": "Others"
                }
            ]
        },
        {
            "id": 12473,
            "key": "visible_to",
            "name": "Visible to",
            "group_id": null,
            "order_nr": 0,
            "field_type": "visible_to",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": 0,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": 1,
                    "label": "Item owner"
                },
                {
                    "id": 3,
                    "label": "Item owner’s visibility group"
                },
                {
                    "id": 5,
                    "label": "Item owner’s visibility group and sub-groups"
                },
                {
                    "id": 7,
                    "label": "All users"
                }
            ]
        },
        {
            "id": 12475,
            "key": "activities_count",
            "name": "Total activities",
            "group_id": null,
            "order_nr": 0,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12476,
            "key": "done_activities_count",
            "name": "Done activities",
            "group_id": null,
            "order_nr": 0,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12477,
            "key": "undone_activities_count",
            "name": "Activities to do",
            "group_id": null,
            "order_nr": 0,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12478,
            "key": "email_messages_count",
            "name": "Email messages count",
            "group_id": null,
            "order_nr": 0,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12483,
            "key": "product_quantity",
            "name": "Product quantity",
            "group_id": null,
            "order_nr": 0,
            "field_type": "double",
            "json_column_flag": false,
            "add_time": "2019-06-14 09:22:12",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": false,
            "sortable_flag": false,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12484,
            "key": "product_amount",
            "name": "Product amount",
            "group_id": null,
            "order_nr": 0,
            "field_type": "double",
            "json_column_flag": false,
            "add_time": "2019-06-14 09:22:12",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": false,
            "sortable_flag": false,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12501,
            "key": "product_name",
            "name": "Product name",
            "group_id": null,
            "order_nr": 0,
            "field_type": "varchar",
            "json_column_flag": false,
            "add_time": "2023-05-27 08:19:39",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": false,
            "sortable_flag": false,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12505,
            "key": "mrr",
            "name": "MRR",
            "group_id": null,
            "order_nr": 0,
            "field_type": "monetary",
            "json_column_flag": false,
            "add_time": "2024-05-06 09:29:01",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": null,
            "key": "mrr_currency",
            "name": "Currency of MRR",
            "field_type": "varchar",
            "edit_flag": false,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": true,
            "parent_id": 12505,
            "id_suffix": "currency"
        },
        {
            "id": 12506,
            "key": "arr",
            "name": "ARR",
            "group_id": null,
            "order_nr": 0,
            "field_type": "monetary",
            "json_column_flag": false,
            "add_time": "2024-05-06 09:29:01",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": null,
            "key": "arr_currency",
            "name": "Currency of ARR",
            "field_type": "varchar",
            "edit_flag": false,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": true,
            "parent_id": 12506,
            "id_suffix": "currency"
        },
        {
            "id": 12507,
            "key": "acv",
            "name": "ACV",
            "group_id": null,
            "order_nr": 0,
            "field_type": "monetary",
            "json_column_flag": false,
            "add_time": "2024-05-06 09:29:01",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": null,
            "key": "acv_currency",
            "name": "Currency of ACV",
            "field_type": "varchar",
            "edit_flag": false,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": true,
            "parent_id": 12507,
            "id_suffix": "currency"
        },
        {
            "id": 12508,
            "key": "origin",
            "name": "Source origin",
            "group_id": null,
            "order_nr": 0,
            "field_type": "enum",
            "json_column_flag": false,
            "add_time": "2024-05-28 21:57:30",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": "ManuallyCreated",
                    "label": "Manually created"
                },
                {
                    "id": "Import",
                    "label": "Import"
                },
                {
                    "id": "API",
                    "label": "API"
                },
                {
                    "id": "Automation",
                    "label": "Automation"
                },
                {
                    "id": "Marketplace",
                    "label": "Marketplace"
                },
                {
                    "id": "Prospector",
                    "label": "Prospector"
                },
                {
                    "id": "LeadSuggestion",
                    "label": "Lead suggestions"
                },
                {
                    "id": "WebForms",
                    "label": "Web Forms"
                },
                {
                    "id": "Chatbot",
                    "label": "Chatbot"
                },
                {
                    "id": "LiveChat",
                    "label": "Live Chat"
                },
                {
                    "id": "WebVisitors",
                    "label": "Web Visitors"
                },
                {
                    "id": "Campaigns",
                    "label": "Campaigns"
                },
                {
                    "id": "MessagingInbox",
                    "label": "Messaging inbox"
                }
            ]
        },
        {
            "id": 12509,
            "key": "origin_id",
            "name": "Source origin ID",
            "group_id": null,
            "order_nr": 0,
            "field_type": "varchar",
            "json_column_flag": false,
            "add_time": "2024-05-28 21:57:30",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12510,
            "key": "channel",
            "name": "Source channel",
            "group_id": null,
            "order_nr": 0,
            "field_type": "enum",
            "json_column_flag": false,
            "add_time": "2024-05-28 21:57:30",
            "update_time": "2025-07-04 08:42:54",
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": 64,
                    "label": "Prospector",
                    "alt_id": "prospector"
                },
                {
                    "id": 65,
                    "label": "Lead Suggestions",
                    "alt_id": "lead_suggestions"
                },
                {
                    "id": 66,
                    "label": "Web forms",
                    "alt_id": "web_forms"
                },
                {
                    "id": 67,
                    "label": "Chatbot",
                    "alt_id": "chatbot"
                },
                {
                    "id": 68,
                    "label": "Live chat",
                    "alt_id": "live_chat"
                },
                {
                    "id": 69,
                    "label": "Web visitors",
                    "alt_id": "web_visitors"
                },
                {
                    "id": 70,
                    "label": "Campaigns",
                    "alt_id": "campaigns"
                },
                {
                    "id": 71,
                    "label": "Marketplace",
                    "alt_id": "marketplace"
                },
                {
                    "id": 72,
                    "label": "Messaging Inbox",
                    "alt_id": "messaging_inbox"
                }
            ]
        },
        {
            "id": 12511,
            "key": "channel_id",
            "name": "Source channel ID",
            "group_id": null,
            "order_nr": 0,
            "field_type": "varchar",
            "json_column_flag": false,
            "add_time": "2024-05-28 21:57:30",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12521,
            "key": "is_archived",
            "name": "Archive status",
            "group_id": null,
            "order_nr": 0,
            "field_type": "enum",
            "json_column_flag": false,
            "add_time": "2025-03-25 11:03:30",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": false,
                    "label": "Not archived"
                },
                {
                    "id": true,
                    "label": "Archived"
                }
            ]
        },
        {
            "id": 12522,
            "key": "archive_time",
            "name": "Archive time",
            "group_id": null,
            "order_nr": 0,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2025-03-25 11:03:30",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12527,
            "key": "score",
            "name": "Score",
            "group_id": null,
            "order_nr": 0,
            "field_type": "double",
            "json_column_flag": false,
            "add_time": "2025-11-18 10:36:48",
            "update_time": null,
            "last_updated_by_user_id": null,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12524,
            "key": "sequence_enrollment",
            "name": "Sequence enrollment",
            "group_id": 1,
            "order_nr": 1,
            "field_type": "boolean",
            "json_column_flag": false,
            "add_time": "2025-07-04 10:29:15",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": false,
            "sortable_flag": false,
            "mandatory_flag": true,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12454,
            "key": "value",
            "name": "Value",
            "group_id": 1,
            "order_nr": 2,
            "field_type": "monetary",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": null,
            "key": "currency",
            "name": "Currency",
            "field_type": "varchar",
            "edit_flag": false,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": false,
            "parent_id": 12454,
            "id_suffix": "currency"
        },
        {
            "id": 12456,
            "key": "probability",
            "name": "Probability",
            "group_id": 1,
            "order_nr": 3,
            "field_type": "int",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": false,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": false,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12457,
            "key": "org_id",
            "name": "Organization",
            "group_id": 1,
            "order_nr": 4,
            "field_type": "org",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": {
                "person_id": "<=0"
            },
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12459,
            "key": "person_id",
            "name": "Contact person",
            "group_id": 1,
            "order_nr": 5,
            "field_type": "people",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": {
                "org_id": "<=0"
            },
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12479,
            "key": "expected_close_date",
            "name": "Expected close date",
            "group_id": 1,
            "order_nr": 6,
            "field_type": "date",
            "json_column_flag": false,
            "add_time": "2019-06-09 10:23:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true
            }
        },
        {
            "id": 12492,
            "key": "label",
            "name": "Label",
            "group_id": 1,
            "order_nr": 7,
            "field_type": "set",
            "json_column_flag": false,
            "add_time": "2020-02-12 05:05:46",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": false,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": false,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": true,
            "show_in_pipelines": {
                "show_in_all": true
            },
            "options": [
                {
                    "id": 56,
                    "label": "target",
                    "color": "blue"
                }
            ]
        },
        {
            "id": 12514,
            "key": "4f2f060aaa56536fb78c5d1038ab56a24b8ebc63",
            "name": "PO no.",
            "group_id": null,
            "order_nr": 8,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2024-11-10 06:47:21",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12513,
            "key": "5ffea68859bd7089ce52f603ee5f88c14b3ff260",
            "name": "Location",
            "group_id": null,
            "order_nr": 9,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2024-11-10 06:46:23",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12490,
            "key": "aaff5efec614d2cd18aecdfa5f800af9167cac1d",
            "name": "Deadline",
            "group_id": null,
            "order_nr": 10,
            "field_type": "date",
            "json_column_flag": true,
            "add_time": "2020-01-29 18:38:59",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": true,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": "",
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12496,
            "key": "bd7bb3b2758ca81feebf015ca60bf528eafe47f0",
            "name": "End user",
            "group_id": null,
            "order_nr": 11,
            "field_type": "people",
            "json_column_flag": true,
            "add_time": "2021-05-26 10:25:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": "",
            "created_by_user_id": null,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12515,
            "key": "3625266375cf115cf1a0edb6924d5c2c2243d540",
            "name": "Part Number",
            "group_id": null,
            "order_nr": 12,
            "field_type": "set",
            "json_column_flag": true,
            "add_time": "2024-11-11 07:49:15",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            },
            "options": [
                {
                    "id": 82,
                    "label": "Berno-s"
                },
                {
                    "id": 79,
                    "label": "CARPET"
                },
                {
                    "id": 81,
                    "label": "HC229"
                },
                {
                    "id": 80,
                    "label": "Metal-Baffle6"
                },
                {
                    "id": 78,
                    "label": "RFQ"
                },
                {
                    "id": 76,
                    "label": "ST101-30120"
                },
                {
                    "id": 75,
                    "label": "ST101-6060"
                },
                {
                    "id": 77,
                    "label": "ST628-30100"
                },
                {
                    "id": 92,
                    "label": "MONO-FIBER8"
                }
            ]
        },
        {
            "id": 12517,
            "key": "56db4d96acbfa1e19d9d97c3821c3674d3fcaf94",
            "name": "Quantity",
            "group_id": null,
            "order_nr": 13,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2024-11-12 06:53:46",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12520,
            "key": "f71407beeb55195def1dce9326667e7c54f2cb42",
            "name": "Product Type",
            "group_id": null,
            "order_nr": 14,
            "field_type": "set",
            "json_column_flag": true,
            "add_time": "2025-01-08 06:34:35",
            "update_time": "2025-12-01 12:27:05",
            "last_updated_by_user_id": 15733715,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            },
            "options": [
                {
                    "id": 87,
                    "label": "Ceiling Tiles"
                },
                {
                    "id": 88,
                    "label": "Baffle Ceiling"
                },
                {
                    "id": 89,
                    "label": "Carpet"
                },
                {
                    "id": 90,
                    "label": "Fitout"
                },
                {
                    "id": 91,
                    "label": "Other"
                },
                {
                    "id": 93,
                    "label": "PET Tiles/Baffles"
                },
                {
                    "id": 94,
                    "label": "Sofa"
                }
            ]
        },
        {
            "id": 12528,
            "key": "64f9afd3d69fc32e006ddbd7736cb0e945faf421",
            "name": "Remaining amount (If invoiced)",
            "group_id": null,
            "order_nr": 15,
            "field_type": "monetary",
            "json_column_flag": true,
            "add_time": "2025-12-17 12:23:49",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 9373337,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": null,
            "key": "64f9afd3d69fc32e006ddbd7736cb0e945faf421_currency",
            "name": "Currency of Remaining amount (If invoiced)",
            "field_type": "varchar",
            "edit_flag": true,
            "active_flag": true,
            "is_subfield": true,
            "mandatory_flag": false,
            "parent_id": 12528,
            "id_suffix": "currency"
        },
        {
            "id": 12526,
            "key": "c0323a114651cc691e866bdb1d840971d60626ba",
            "name": "Expected Finishin Date",
            "group_id": null,
            "order_nr": 16,
            "field_type": "date",
            "json_column_flag": true,
            "add_time": "2025-11-10 12:41:33",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 9373337,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12525,
            "key": "d1e4bd92930d9b18d8bf44542310ab1bea9ad475",
            "name": "Product Type/Category",
            "group_id": 3,
            "order_nr": 18,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2025-07-15 06:42:02",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12523,
            "key": "b09660187f2c3c9df39c11439fb69ca9f582e383",
            "name": "Remarks",
            "group_id": 3,
            "order_nr": 19,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2025-06-25 07:55:32",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12516,
            "key": "fdee83bde897e7e1477bb47e6d15bedb4272eb40",
            "name": "TOTAL SAR VALUE",
            "group_id": 3,
            "order_nr": 20,
            "field_type": "double",
            "json_column_flag": true,
            "add_time": "2024-11-12 05:31:27",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        },
        {
            "id": 12518,
            "key": "04196647566da4208c39be12ecc6044ac3b1cef3",
            "name": "Contact no.",
            "group_id": 3,
            "order_nr": 21,
            "field_type": "varchar",
            "json_column_flag": true,
            "add_time": "2024-11-14 10:14:46",
            "update_time": "2025-12-17 12:24:31",
            "last_updated_by_user_id": 9373337,
            "edit_flag": true,
            "details_visible_flag": true,
            "add_visible_flag": false,
            "important_flag": false,
            "bulk_edit_allowed": true,
            "filtering_allowed": true,
            "sortable_flag": true,
            "mandatory_flag": false,
            "searchable_flag": true,
            "restriction_settings": [],
            "user_restrictions": null,
            "description": null,
            "created_by_user_id": 13459159,
            "active_flag": true,
            "projects_detail_visible_flag": false,
            "show_in_pipelines": {
                "show_in_all": true,
                "pipeline_ids": []
            }
        }
    ],
    "additional_data": {
        "pagination": {
            "start": 0,
            "limit": 500,
            "more_items_in_collection": false
        }
    }
}

```

# Deal stages and thier id and information

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "order_nr": 1,
            "name": "Lead In",
            "active_flag": true,
            "deal_probability": 10,
            "pipeline_id": 1,
            "rotten_flag": true,
            "rotten_days": 30,
            "add_time": "2019-06-09 10:51:11",
            "update_time": "2021-05-22 07:32:01",
            "pipeline_name": "Pipeline",
            "pipeline_deal_probability": true
        },
        {
            "id": 2,
            "order_nr": 2,
            "name": "Enquiry",
            "active_flag": true,
            "deal_probability": 20,
            "pipeline_id": 1,
            "rotten_flag": true,
            "rotten_days": 30,
            "add_time": "2019-06-09 10:51:11",
            "update_time": "2021-05-22 07:32:01",
            "pipeline_name": "Pipeline",
            "pipeline_deal_probability": true
        },
        {
            "id": 3,
            "order_nr": 3,
            "name": "Quotation",
            "active_flag": true,
            "deal_probability": 20,
            "pipeline_id": 1,
            "rotten_flag": true,
            "rotten_days": 30,
            "add_time": "2019-06-09 10:51:11",
            "update_time": "2021-05-22 07:32:01",
            "pipeline_name": "Pipeline",
            "pipeline_deal_probability": true
        },
        {
            "id": 4,
            "order_nr": 4,
            "name": "Submittal",
            "active_flag": true,
            "deal_probability": 80,
            "pipeline_id": 1,
            "rotten_flag": true,
            "rotten_days": 15,
            "add_time": "2019-06-09 10:51:11",
            "update_time": "2021-05-22 07:32:01",
            "pipeline_name": "Pipeline",
            "pipeline_deal_probability": true
        },
        {
            "id": 5,
            "order_nr": 5,
            "name": "Production /Supplying",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 1,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2019-06-09 10:51:11",
            "update_time": "2021-05-22 07:32:01",
            "pipeline_name": "Pipeline",
            "pipeline_deal_probability": true
        },
        {
            "id": 14,
            "order_nr": 1,
            "name": "RFQ Recieved",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2020-01-26 07:49:40",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 15,
            "order_nr": 2,
            "name": "RFQ Sent",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2020-01-26 07:49:40",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 16,
            "order_nr": 3,
            "name": "Price Recieved",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2020-01-26 07:49:40",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 46,
            "order_nr": 4,
            "name": "Awaiting approval",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2021-12-21 09:10:50",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 47,
            "order_nr": 5,
            "name": "Approved by Manager",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2021-12-21 09:10:50",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 17,
            "order_nr": 6,
            "name": "Extension",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2020-01-26 07:49:40",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 18,
            "order_nr": 7,
            "name": "Proposal Submitted",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 3,
            "rotten_flag": true,
            "rotten_days": 10,
            "add_time": "2020-01-26 07:49:40",
            "update_time": "2023-11-01 09:13:28",
            "pipeline_name": "Aramco Inquiries",
            "pipeline_deal_probability": true
        },
        {
            "id": 19,
            "order_nr": 1,
            "name": "Aramco Issued PO",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-04-28 10:57:57",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 20,
            "order_nr": 2,
            "name": "PO Sent to Supplier",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-04-28 10:57:57",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 21,
            "order_nr": 3,
            "name": "Awaiting Payment",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-04-28 10:57:57",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 34,
            "order_nr": 4,
            "name": "Awaiting Shipping (PAID)",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-03-02 12:36:00",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 22,
            "order_nr": 5,
            "name": "in transit",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-04-28 10:57:57",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 33,
            "order_nr": 6,
            "name": "In customs",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-03-02 12:36:00",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 48,
            "order_nr": 7,
            "name": "HOLD",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2022-03-10 07:21:43",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 23,
            "order_nr": 8,
            "name": "Arrived ",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-04-28 10:57:57",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 24,
            "order_nr": 9,
            "name": "ASN",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-07-06 11:07:03",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 25,
            "order_nr": 10,
            "name": "Pending GR",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 4,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-07-06 11:07:03",
            "update_time": "2022-05-18 11:31:34",
            "pipeline_name": "Aramco PO",
            "pipeline_deal_probability": false
        },
        {
            "id": 50,
            "order_nr": 1,
            "name": "Lead In",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2022-10-05 06:43:23",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 27,
            "order_nr": 2,
            "name": "Order Received",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-11-10 12:33:09",
            "update_time": "2024-11-06 08:48:37",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 49,
            "order_nr": 3,
            "name": "Stuck/To be Canceled",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2022-08-22 07:39:30",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 28,
            "order_nr": 4,
            "name": "Approved",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-11-10 12:33:09",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 29,
            "order_nr": 5,
            "name": "Awaiting Payment",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-11-10 12:33:09",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 44,
            "order_nr": 6,
            "name": "Awaiting Site Readiness",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-11-03 16:14:06",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 45,
            "order_nr": 7,
            "name": "Everything Read but not started",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-11-03 16:14:06",
            "update_time": "2023-03-22 13:10:04",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 30,
            "order_nr": 8,
            "name": "Underprogress",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-11-10 12:33:09",
            "update_time": "2024-10-27 06:48:57",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 82,
            "order_nr": 9,
            "name": "Awaiting MDD",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2024-04-22 08:58:28",
            "update_time": "2024-11-06 08:50:28",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 42,
            "order_nr": 10,
            "name": "Awaiting GCC",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-08-12 09:17:22",
            "update_time": "2024-11-06 08:50:28",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 43,
            "order_nr": 11,
            "name": "Awaiting GR",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 5,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-08-15 09:32:29",
            "update_time": "2024-10-27 06:48:57",
            "pipeline_name": "Aramco Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 9,
            "order_nr": 1,
            "name": "Target/Research",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-01-25 16:57:59",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 38,
            "order_nr": 2,
            "name": "Initial Contact Made",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-05-24 11:35:23",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 40,
            "order_nr": 3,
            "name": "First Meeting ",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-06-07 11:34:20",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 10,
            "order_nr": 4,
            "name": "Second Meeting(Interested)",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-01-25 16:57:59",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 39,
            "order_nr": 5,
            "name": "Follow up 1",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-06-07 11:29:41",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 11,
            "order_nr": 6,
            "name": "Second Follow up 2",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-01-25 16:57:59",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 12,
            "order_nr": 7,
            "name": "Not Ready to buy",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 2,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2020-01-25 16:57:59",
            "update_time": "2023-02-13 07:07:28",
            "pipeline_name": "Prospecting",
            "pipeline_deal_probability": false
        },
        {
            "id": 35,
            "order_nr": 1,
            "name": "Bidding",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 6,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-05-22 07:27:01",
            "update_time": "2021-05-22 07:27:26",
            "pipeline_name": "Bidding Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 36,
            "order_nr": 2,
            "name": "ON HOLD",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 6,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-05-22 07:27:01",
            "update_time": "2021-05-22 07:27:26",
            "pipeline_name": "Bidding Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 37,
            "order_nr": 3,
            "name": "Contract Awarded",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 6,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2021-05-22 07:27:01",
            "update_time": "2021-05-22 07:27:26",
            "pipeline_name": "Bidding Projects",
            "pipeline_deal_probability": true
        },
        {
            "id": 78,
            "order_nr": 1,
            "name": "Pre-design - Data collection",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 10,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2024-01-17 06:31:01",
            "update_time": "2024-01-17 06:31:01",
            "pipeline_name": "Design Development",
            "pipeline_deal_probability": false
        },
        {
            "id": 80,
            "order_nr": 2,
            "name": "Cost Estimation & 2D Layout",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 10,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2024-01-17 06:31:01",
            "update_time": "2024-01-18 05:14:24",
            "pipeline_name": "Design Development",
            "pipeline_deal_probability": false
        },
        {
            "id": 79,
            "order_nr": 3,
            "name": "Revision and finalization",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 10,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2024-01-17 06:31:01",
            "update_time": "2024-01-18 05:14:24",
            "pipeline_name": "Design Development",
            "pipeline_deal_probability": false
        },
        {
            "id": 81,
            "order_nr": 4,
            "name": "Completed",
            "active_flag": true,
            "deal_probability": 100,
            "pipeline_id": 10,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2024-01-18 05:13:54",
            "update_time": "2024-01-18 05:13:54",
            "pipeline_name": "Design Development",
            "pipeline_deal_probability": false
        },
        {
            "id": 85,
            "order_nr": 1,
            "name": "Gathering Documents",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 11,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2025-05-26 09:38:40",
            "update_time": "2025-05-26 09:38:40",
            "pipeline_name": "Problematic & Stuck Orders",
            "pipeline_deal_probability": true
        },
        {
            "id": 83,
            "order_nr": 2,
            "name": "Underprogress",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 11,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2025-05-26 09:38:40",
            "update_time": "2025-05-26 09:38:40",
            "pipeline_name": "Problematic & Stuck Orders",
            "pipeline_deal_probability": true
        },
        {
            "id": 84,
            "order_nr": 3,
            "name": "Awaiting Resolution",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 11,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2025-05-26 09:38:40",
            "update_time": "2025-05-26 09:38:40",
            "pipeline_name": "Problematic & Stuck Orders",
            "pipeline_deal_probability": true
        },
        {
            "id": 86,
            "order_nr": 4,
            "name": "Almost Dead",
            "active_flag": true,
            "deal_probability": 0,
            "pipeline_id": 11,
            "rotten_flag": false,
            "rotten_days": null,
            "add_time": "2025-05-26 09:38:40",
            "update_time": "2025-05-26 09:38:40",
            "pipeline_name": "Problematic & Stuck Orders",
            "pipeline_deal_probability": true
        }
    ],
    "additional_data": {
        "pagination": {
            "start": 0,
            "limit": 100,
            "more_items_in_collection": false
        }
    }
}
```

# Deals update for flow (List the movement of a deal)
GET /v1/deals/3769/flow?start=0&all_changes=1
This is the schema returned by the api

```json
{
    "success": true,
    "data": [
        {
            "object": "activity",
            "timestamp": "2024-07-04 00:00:00",
            "data": {
                "id": 20972,
                "user_id": 9392603,
                "done": false,
                "type": "call",
                "reference_type": null,
                "reference_id": null,
                "conference_meeting_client": null,
                "conference_meeting_url": null,
                "due_date": "2024-07-04",
                "due_time": "",
                "duration": "",
                "busy_flag": false,
                "add_time": "2024-07-02 11:16:54",
                "marked_as_done_time": "",
                "last_notification_time": null,
                "last_notification_user_id": null,
                "notification_language_id": null,
                "subject": "following up email",
                "public_description": "",
                "calendar_sync_include_context": null,
                "location": null,
                "org_id": 2220,
                "person_id": 7620,
                "deal_id": 3769,
                "lead_id": null,
                "project_id": null,
                "active_flag": true,
                "update_time": "2024-07-02 11:16:54",
                "update_user_id": null,
                "source_timezone": null,
                "rec_rule": null,
                "rec_rule_extension": null,
                "rec_master_activity_id": null,
                "conference_meeting_id": null,
                "original_start_time": null,
                "private": false,
                "priority": null,
                "note": "following up her email&nbsp;",
                "created_by_user_id": 9392603,
                "location_subpremise": null,
                "location_street_number": null,
                "location_route": null,
                "location_sublocality": null,
                "location_locality": null,
                "location_admin_area_level_1": null,
                "location_admin_area_level_2": null,
                "location_country": null,
                "location_postal_code": null,
                "location_formatted_address": null,
                "attendees": null,
                "participants": [
                    {
                        "person_id": 7620,
                        "primary_flag": true
                    }
                ],
                "series": null,
                "is_recurring": null,
                "org_name": "Saudi  Aramco",
                "person_name": "Babidan, Mohammad",
                "deal_title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY",
                "lead_title": null,
                "project_title": null,
                "owner_name": "Arshad Kamal",
                "person_dropbox_bcc": "gyptech-568b5d@pipedrivemail.com",
                "deal_dropbox_bcc": "gyptech-568b5d+deal3769@pipedrivemail.com",
                "assigned_to_user_id": 9392603,
                "type_name": "Call",
                "lead": null,
                "company_id": 6191422
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-11-10 12:44:25",
            "data": {
                "id": 100983,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "f71407beeb55195def1dce9326667e7c54f2cb42",
                "old_value": "85",
                "new_value": null,
                "is_bulk_update_flag": 1,
                "log_time": "2025-11-10 12:44:25",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "bulkAction",
                "origin_id": "5540587",
                "additional_data": []
            }
        },
        {
            "object": "note",
            "timestamp": "2025-09-14 11:34:31",
            "data": {
                "id": 39341,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/9392643\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9392643\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Talha Waseem</a>&nbsp;as per our discussion , you are assigned to handle this project. Please take care of the site visit for actual site measurement. Thank you. <a href=\"/users/details/16532823\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:16532823\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@ABDUL BASITH</a>&nbsp;<a href=\"/users/details/9373337\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9373337\" data-mentions-you=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Mohammed Alhashim</a>&nbsp; <a href=\"/users/details/9392603\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9392603\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Arshad Kamal</a>&nbsp;",
                "add_time": "2025-09-14 11:34:31",
                "update_time": "2025-09-14 11:34:47",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:31:17",
            "data": {
                "id": 99966,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_change_time",
                "old_value": "2025-02-25 10:26:37",
                "new_value": "2025-09-14 11:31:17",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:31:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:31:17",
            "data": {
                "id": 99965,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_id",
                "old_value": "49",
                "new_value": "28",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:31:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Stuck/To be Canceled",
                    "new_value_formatted": "Approved"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:30:20",
            "data": {
                "id": 99964,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "9392603",
                "new_value": "9392643",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:30:20",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Arshad Kamal",
                    "new_value_formatted": "Talha Waseem"
                }
            }
        },
        {
            "object": "mailMessage",
            "timestamp": "2025-09-11 12:50:40",
            "data": {
                "id": 350228,
                "from": [
                    {
                        "id": 143517,
                        "email_address": "arshadkamal@gyptech.com.sa",
                        "name": "Arshad Kamal",
                        "linked_person_id": 8658,
                        "linked_person_name": "Arshadkamal",
                        "mail_message_party_id": 297022
                    }
                ],
                "to": [
                    {
                        "id": 143514,
                        "email_address": "faris@gyptech.com.sa",
                        "name": "Faris Alhashim",
                        "linked_person_id": 8657,
                        "linked_person_name": "Faris",
                        "mail_message_party_id": 297023
                    },
                    {
                        "id": 143515,
                        "email_address": "mohd@gyptech.com.sa",
                        "name": "Mohammed Alhashim",
                        "linked_person_id": 8652,
                        "linked_person_name": "Mohd",
                        "mail_message_party_id": 297031
                    },
                    {
                        "id": 143521,
                        "email_address": "mshoaibaslam@gyptech.com.sa",
                        "name": "Shoaib Aslam",
                        "linked_person_id": 8656,
                        "linked_person_name": "Mshoaibaslam",
                        "mail_message_party_id": 297024
                    },
                    {
                        "id": 143524,
                        "email_address": "jay@gyptech.com.sa",
                        "name": "Jay Mar C. Flor",
                        "linked_person_id": 8660,
                        "linked_person_name": "Jay",
                        "mail_message_party_id": 297030
                    },
                    {
                        "id": 143543,
                        "email_address": "talha@gyptech.com.sa",
                        "name": "Talha Waseem",
                        "linked_person_id": 8684,
                        "linked_person_name": "Talha",
                        "mail_message_party_id": 297026
                    },
                    {
                        "id": 143681,
                        "email_address": "areej@gyptech.com.sa",
                        "name": "Areej Alhashim",
                        "linked_person_id": 8730,
                        "linked_person_name": "Areej",
                        "mail_message_party_id": 297028
                    },
                    {
                        "id": 143765,
                        "email_address": "ramlah.alabdulmohsen@aramco.com",
                        "name": "Ramlah A",
                        "linked_person_id": 8036,
                        "linked_person_name": "Ms. Ramlah Alabdulmohsen",
                        "mail_message_party_id": 297032
                    },
                    {
                        "id": 143793,
                        "email_address": "felino@gyptech.com.sa",
                        "name": "Felino",
                        "linked_person_id": 8735,
                        "linked_person_name": "Felino",
                        "mail_message_party_id": 297027
                    },
                    {
                        "id": 146165,
                        "email_address": "syed@gyptech.com.sa",
                        "name": "Syed Nooman Nehal",
                        "linked_person_id": 9347,
                        "linked_person_name": "Syed",
                        "mail_message_party_id": 297025
                    },
                    {
                        "id": 147527,
                        "email_address": "rani.ladines@aramco.com",
                        "name": "Rani V",
                        "linked_person_id": 8113,
                        "linked_person_name": "Mr. Ladines, Rani V",
                        "mail_message_party_id": 297029
                    },
                    {
                        "id": 147581,
                        "email_address": "gyptech-568b5d+deal3769@pipedrivemail.com",
                        "name": "",
                        "linked_person_id": null,
                        "linked_person_name": null,
                        "mail_message_party_id": 297033
                    }
                ],
                "cc": [],
                "bcc": [],
                "body_url": "?Expires=0",
                "nylas_id": null,
                "account_id": null,
                "user_id": 13459159,
                "mail_thread_id": 32783,
                "subject": "Fw: Follow-Up on PO_4506904380",
                "snippet": "________________________________\r\nFrom: Arshad Kamal <Arshadkamal@gyptech.com.sa>\r\nSent: Thursday, September 11, 2025 3:10 PM\r\nTo: Alabdulmohsen, Ramlah A <ramlah.alabdulmohsen@aramco.com>\r\nCc: Mohammed Alhashim <mohd@gyptech",
                "mail_tracking_status": null,
                "mail_link_tracking_enabled_flag": 0,
                "mail_link_tracking_last_clicked_at": null,
                "read_flag": 0,
                "draft": null,
                "wa_meta": null,
                "s3_bucket": "pipedrive-mail-lon-2-pipedrive-com",
                "s3_bucket_path": "c426-6191422/13459159/nylas/32783/350228/body",
                "draft_flag": 0,
                "synced_flag": 1,
                "deleted_flag": 0,
                "external_deleted_flag": 0,
                "expunged_flag": 0,
                "has_body_flag": 1,
                "sent_flag": 0,
                "sent_from_pipedrive_flag": 0,
                "smart_bcc_flag": 1,
                "message_time": "2025-09-11T12:50:40.000Z",
                "add_time": "2025-09-11T12:50:40.000Z",
                "update_time": "2025-09-11T12:50:40.000Z",
                "has_attachments_flag": 0,
                "has_inline_attachments_flag": 0,
                "has_real_attachments_flag": 0,
                "group_sending_flag": 0,
                "mua_message_id": "<DB4PR03MB8514C575B202A281D06A7C968F09A@DB4PR03MB8514.eurprd03.prod.outlook.com>",
                "in_reply_to": null,
                "last_replied_at": null,
                "template_id": null,
                "mail_queue": [],
                "mail_signature_id": null,
                "deal_id": 3769,
                "lead_id": null,
                "project_id": null,
                "connection_type": "private",
                "team_admin_user_id": null,
                "sender_user_id": null,
                "item_type": "mailMessage",
                "timestamp": "2025-09-11T12:50:40.000Z",
                "company_id": 6191422
            }
        },
        {
            "object": "mailMessage",
            "timestamp": "2025-09-11 12:50:23",
            "data": {
                "id": 350227,
                "from": [
                    {
                        "id": 143765,
                        "email_address": "ramlah.alabdulmohsen@aramco.com",
                        "name": "Ramlah A",
                        "linked_person_id": 8036,
                        "linked_person_name": "Ms. Ramlah Alabdulmohsen",
                        "mail_message_party_id": 297015
                    }
                ],
                "to": [
                    {
                        "id": 143515,
                        "email_address": "mohd@gyptech.com.sa",
                        "name": "Mohammed Alhashim",
                        "linked_person_id": 8652,
                        "linked_person_name": "Mohd",
                        "mail_message_party_id": 297018
                    },
                    {
                        "id": 143517,
                        "email_address": "arshadkamal@gyptech.com.sa",
                        "name": "Arshad Kamal",
                        "linked_person_id": 8658,
                        "linked_person_name": "Arshadkamal",
                        "mail_message_party_id": 297020
                    },
                    {
                        "id": 143524,
                        "email_address": "jay@gyptech.com.sa",
                        "name": "Jay Mar C. Flor",
                        "linked_person_id": 8660,
                        "linked_person_name": "Jay",
                        "mail_message_party_id": 297017
                    },
                    {
                        "id": 143681,
                        "email_address": "areej@gyptech.com.sa",
                        "name": "Areej Alhashim",
                        "linked_person_id": 8730,
                        "linked_person_name": "Areej",
                        "mail_message_party_id": 297019
                    },
                    {
                        "id": 147527,
                        "email_address": "rani.ladines@aramco.com",
                        "name": "Rani V",
                        "linked_person_id": 8113,
                        "linked_person_name": "Mr. Ladines, Rani V",
                        "mail_message_party_id": 297016
                    },
                    {
                        "id": 147581,
                        "email_address": "gyptech-568b5d+deal3769@pipedrivemail.com",
                        "name": "",
                        "linked_person_id": null,
                        "linked_person_name": null,
                        "mail_message_party_id": 297021
                    }
                ],
                "cc": [],
                "bcc": [],
                "body_url": "?Expires=0",
                "nylas_id": null,
                "account_id": null,
                "user_id": 13459159,
                "mail_thread_id": 32782,
                "subject": "Fw: Follow-Up on PO_4506904380",
                "snippet": "\r\n\r\n\r\n________________________________\r\nFrom: Alabdulmohsen, Ramlah A <ramlah.alabdulmohsen@aramco.com>\r\nSent: Thursday, September 11, 2025 8:10 AM\r\nTo: Arshad Kamal <Arshadkamal@gyptech.com.sa>; Areej Alhashim <areej@gyptech",
                "mail_tracking_status": null,
                "mail_link_tracking_enabled_flag": 0,
                "mail_link_tracking_last_clicked_at": null,
                "read_flag": 0,
                "draft": null,
                "wa_meta": null,
                "s3_bucket": "pipedrive-mail-lon-2-pipedrive-com",
                "s3_bucket_path": "c426-6191422/13459159/nylas/32782/350227/body",
                "draft_flag": 0,
                "synced_flag": 1,
                "deleted_flag": 0,
                "external_deleted_flag": 0,
                "expunged_flag": 0,
                "has_body_flag": 1,
                "sent_flag": 0,
                "sent_from_pipedrive_flag": 0,
                "smart_bcc_flag": 1,
                "message_time": "2025-09-11T12:50:23.000Z",
                "add_time": "2025-09-11T12:50:22.000Z",
                "update_time": "2025-09-11T12:50:23.000Z",
                "has_attachments_flag": 1,
                "has_inline_attachments_flag": 0,
                "has_real_attachments_flag": 1,
                "group_sending_flag": 0,
                "mua_message_id": "<DB4PR03MB8514315F8742ADD2849F265F8F09A@DB4PR03MB8514.eurprd03.prod.outlook.com>",
                "in_reply_to": null,
                "last_replied_at": null,
                "template_id": null,
                "mail_queue": [],
                "mail_signature_id": null,
                "deal_id": 3769,
                "lead_id": null,
                "project_id": null,
                "connection_type": "private",
                "team_admin_user_id": null,
                "sender_user_id": null,
                "item_type": "mailMessage",
                "timestamp": "2025-09-11T12:50:22.000Z",
                "company_id": 6191422
            }
        },
        {
            "object": "note",
            "timestamp": "2025-09-11 12:27:59",
            "data": {
                "id": 39334,
                "user_id": 15733715,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/16532823\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"15733715:16532823\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@ABDUL BASITH</a>&nbsp;Kindly check portal status",
                "add_time": "2025-09-11 12:27:59",
                "update_time": "2025-09-11 12:27:59",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "ye@gyptech.com.sa",
                    "name": "Ye Myint Htun",
                    "icon_url": null,
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2025-06-15 12:33:25",
            "data": {
                "id": 38229,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/9392603\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9392603\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Arshad Kamal</a>&nbsp;",
                "add_time": "2025-06-15 12:33:25",
                "update_time": "2025-06-15 12:33:25",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-06-15 12:33:13",
            "data": {
                "id": 96632,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "15453699",
                "new_value": "9392603",
                "is_bulk_update_flag": null,
                "log_time": "2025-06-15 12:33:13",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Arshad Kamal",
                    "old_value_formatted": "hind battyour"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-02-25 10:26:37",
            "data": {
                "id": 94593,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "stage_change_time",
                "old_value": "2024-10-22 12:48:44",
                "new_value": "2025-02-25 10:26:37",
                "is_bulk_update_flag": null,
                "log_time": "2025-02-25 10:26:37",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-02-25 10:26:37",
            "data": {
                "id": 94592,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "stage_id",
                "old_value": "45",
                "new_value": "49",
                "is_bulk_update_flag": null,
                "log_time": "2025-02-25 10:26:37",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Everything Read but not started",
                    "new_value_formatted": "Stuck/To be Canceled"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-01-13 10:47:00",
            "data": {
                "id": 93905,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "f71407beeb55195def1dce9326667e7c54f2cb42",
                "old_value": null,
                "new_value": "85",
                "is_bulk_update_flag": null,
                "log_time": "2025-01-13 10:47:00",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "note",
            "timestamp": "2024-11-21 08:09:28",
            "data": {
                "id": 36387,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/15453699\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"20601637:15453699\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@hind battyour</a>&nbsp;Kindly provide the latest progress update and the contact information for the specified end-user. Thank you.",
                "add_time": "2024-11-21 08:09:28",
                "update_time": "2024-11-21 08:09:28",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-11-12 11:21:08",
            "data": {
                "id": 36014,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/15453699\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"20601637:15453699\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@hind battyour</a>&nbsp;Please advise the latest progress&nbsp;update for this PO. Thank you",
                "add_time": "2024-11-12 11:21:08",
                "update_time": "2024-11-12 11:21:08",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-12 07:04:40",
            "data": {
                "id": 89367,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "56db4d96acbfa1e19d9d97c3821c3674d3fcaf94",
                "old_value": null,
                "new_value": "Multiple",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-12 07:04:40",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-12 06:28:53",
            "data": {
                "id": 89348,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "fdee83bde897e7e1477bb47e6d15bedb4272eb40",
                "old_value": null,
                "new_value": "474360",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-12 06:28:53",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-11 09:46:48",
            "data": {
                "id": 89137,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "3625266375cf115cf1a0edb6924d5c2c2243d540",
                "old_value": null,
                "new_value": "78",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-11 09:46:48",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-10 08:16:53",
            "data": {
                "id": 88917,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "4f2f060aaa56536fb78c5d1038ab56a24b8ebc63",
                "old_value": null,
                "new_value": "4506904380",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-10 08:16:53",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-10 08:16:50",
            "data": {
                "id": 88916,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "5ffea68859bd7089ce52f603ee5f88c14b3ff260",
                "old_value": null,
                "new_value": "DHAHRAN",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-10 08:16:50",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-06 09:57:57",
            "data": {
                "id": 88656,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "bd7bb3b2758ca81feebf015ca60bf528eafe47f0",
                "old_value": null,
                "new_value": "9850",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-06 09:57:57",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "RAMLAH"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-11-06 09:57:51",
            "data": {
                "id": 35902,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "End-User:&nbsp; RAMLAH",
                "add_time": "2024-11-06 09:57:51",
                "update_time": "2024-11-06 09:57:51",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-11-03 06:46:38",
            "data": {
                "id": 35714,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "Quick Summary: End-user - RAMLAH from OSD. Hind made multiple visits to check ang gather updates about this project. <div><br></div><div><br></div>",
                "add_time": "2024-11-03 06:46:38",
                "update_time": "2024-11-03 06:46:38",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-11-03 06:43:56",
            "data": {
                "id": 35713,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/15453699\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:15453699\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@hind battyour</a>&nbsp; <a href=\"/users/details/9392603\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9392603\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Arshad Kamal</a>&nbsp;<a href=\"/users/details/9373337\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"13459159:9373337\" data-mentions-you=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Mohammed Alhashim</a>&nbsp;- forwarding this PO.&nbsp;",
                "add_time": "2024-11-03 06:43:56",
                "update_time": "2024-11-03 06:43:56",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-03 06:43:50",
            "data": {
                "id": 88425,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "15453699",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-03 06:43:50",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Jay Mar",
                    "new_value_formatted": "hind battyour"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-10-22 12:48:44",
            "data": {
                "id": 87564,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_change_time",
                "old_value": "2024-05-02 03:44:16",
                "new_value": "2024-10-22 12:48:44",
                "is_bulk_update_flag": null,
                "log_time": "2024-10-22 12:48:44",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-10-22 12:48:44",
            "data": {
                "id": 87563,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_id",
                "old_value": "77",
                "new_value": "45",
                "is_bulk_update_flag": null,
                "log_time": "2024-10-22 12:48:44",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Everything Read but not started"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-10-14 12:48:07",
            "data": {
                "id": 35119,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "disccussed in the meeting last October 9.&nbsp; <div><br></div>",
                "add_time": "2024-10-14 12:48:07",
                "update_time": "2024-10-14 12:48:07",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-09-17 07:31:12",
            "data": {
                "id": 34739,
                "user_id": 20698866,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "Please provide any update for this PO <a href=\"/users/details/13459159\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"20698866:13459159\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@Jay Mar</a>&nbsp;",
                "add_time": "2024-09-17 07:31:12",
                "update_time": "2024-09-17 07:31:12",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "prince@gyptech.com.sa",
                    "name": "Prince Lancell Libre",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20698866_683459ea965525062bec769d2868d21f.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-22 07:55:22",
            "data": {
                "id": 85602,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "9392603",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-22 07:55:22",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Jay Mar",
                    "old_value_formatted": "Arshad Kamal"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-22 07:55:07",
            "data": {
                "id": 85601,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "9392603",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-22 07:55:07",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Jay Mar",
                    "new_value_formatted": "Arshad Kamal"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-08-18 11:01:00",
            "data": {
                "id": 34257,
                "user_id": 9392603,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/13459159\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"9392603:13459159\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@Jay Mar</a>&nbsp; &nbsp;latest update Spoke with Ramlah, who is currently in contact with the end user. She is close to persuading them to use wood paneling in the same location. She will notify us of any updates soon.",
                "add_time": "2024-08-18 11:01:00",
                "update_time": "2024-08-18 11:01:00",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "arshadkamal@gyptech.com.sa",
                    "name": "Arshad Kamal",
                    "icon_url": null,
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-18 10:57:31",
            "data": {
                "id": 85412,
                "item_id": 3769,
                "user_id": 9392603,
                "field_key": "user_id",
                "old_value": "12920883",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-18 10:57:31",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Jay Mar",
                    "old_value_formatted": "Abdulrahman"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-08-18 07:26:40",
            "data": {
                "id": 34082,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<div><table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" class=\"page_table\"><colgroup><col width=\"100\" style=\"width:75pt;\"><col width=\"89\" style=\"width:67pt;\"><col width=\"156\" style=\"width:117pt;\"><col width=\"309\" style=\"width:232pt;\"><col width=\"190\" style=\"width:143pt;\"><col width=\"133\" style=\"width:100pt;\"></colgroup><tbody><tr style=\"height:15.75pt;\"><td width=\"100\" height=\"21\" align=\"general\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); border-left-width:1pt; border-left-color:rgb(171, 171, 171); background:white; width:75pt; height:15.75pt;\" valign=\"bottom\">4506904380</td><td width=\"89\" align=\"general\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid none; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); background:white; width:67pt;\" valign=\"bottom\">12/5/2024</td><td width=\"156\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid none; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); background:rgb(220, 190, 34); width:117pt;\" align=\"general\" valign=\"bottom\">Mohammad&nbsp;Babidan</td><td width=\"309\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid none; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); background:white; width:232pt;\" align=\"general\" valign=\"bottom\">No response from end-user- project CRM is cancelled</td><td width=\"190\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid none; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); background:white; width:143pt;\" align=\"general\" valign=\"bottom\">Ramlah Abdulmohsen</td><td width=\"133\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; color:black; font-size:12pt; border-style:none solid solid none; border-right-width:1pt; border-right-color:rgb(171, 171, 171); border-bottom-width:1pt; border-bottom-color:rgb(171, 171, 171); background:white; width:100pt;\" align=\"general\" valign=\"bottom\">Sent on Aug 14</td></tr></tbody></table></div>",
                "add_time": "2024-08-18 07:26:40",
                "update_time": "2024-08-18 07:26:40",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-07-31 12:51:49",
            "data": {
                "id": 33708,
                "user_id": 20698866,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/12920883\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"20698866:12920883\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@Abdulrahman</a>&nbsp;kindly provide update",
                "add_time": "2024-07-31 12:51:49",
                "update_time": "2024-07-31 12:51:49",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "prince@gyptech.com.sa",
                    "name": "Prince Lancell Libre",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20698866_683459ea965525062bec769d2868d21f.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "activity",
            "timestamp": "2024-07-21 00:00:00",
            "data": {
                "id": 21183,
                "user_id": 12920883,
                "done": true,
                "type": "call",
                "reference_type": null,
                "reference_id": null,
                "conference_meeting_client": null,
                "conference_meeting_url": null,
                "due_date": "2024-07-21",
                "due_time": "",
                "duration": "",
                "busy_flag": false,
                "add_time": "2024-07-18 11:32:10",
                "marked_as_done_time": "2024-07-31 13:02:18",
                "last_notification_time": null,
                "last_notification_user_id": null,
                "notification_language_id": null,
                "subject": "follow up with Arshad on Aramco meeting",
                "public_description": "",
                "calendar_sync_include_context": null,
                "location": null,
                "org_id": 2220,
                "person_id": 7620,
                "deal_id": 3769,
                "lead_id": null,
                "project_id": null,
                "active_flag": true,
                "update_time": "2024-07-31 13:02:18",
                "update_user_id": 12920883,
                "source_timezone": null,
                "rec_rule": null,
                "rec_rule_extension": null,
                "rec_master_activity_id": null,
                "conference_meeting_id": null,
                "original_start_time": null,
                "private": false,
                "priority": null,
                "note": null,
                "created_by_user_id": 12920883,
                "location_subpremise": null,
                "location_street_number": null,
                "location_route": null,
                "location_sublocality": null,
                "location_locality": null,
                "location_admin_area_level_1": null,
                "location_admin_area_level_2": null,
                "location_country": null,
                "location_postal_code": null,
                "location_formatted_address": null,
                "attendees": null,
                "participants": [
                    {
                        "person_id": 7620,
                        "primary_flag": true
                    }
                ],
                "series": null,
                "is_recurring": null,
                "org_name": "Saudi  Aramco",
                "person_name": "Babidan, Mohammad",
                "deal_title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY",
                "lead_title": null,
                "project_title": null,
                "owner_name": "Abdulrahman",
                "person_dropbox_bcc": "gyptech-568b5d@pipedrivemail.com",
                "deal_dropbox_bcc": "gyptech-568b5d+deal3769@pipedrivemail.com",
                "assigned_to_user_id": 12920883,
                "type_name": "Call",
                "lead": null,
                "company_id": 6191422
            }
        },
        {
            "object": "note",
            "timestamp": "2024-07-16 07:57:52",
            "data": {
                "id": 33085,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<div><table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" class=\"page_table\"><colgroup><col width=\"129\" style=\"width:97pt;\"><col width=\"132\" style=\"width:99pt;\"><col width=\"102\" style=\"width:77pt;\"><col width=\"315\" style=\"width:236pt;\"><col width=\"211\" style=\"width:158pt;\"><col width=\"177\" style=\"width:133pt;\"></colgroup><tbody><tr style=\"height:30.75pt;\"><td width=\"129\" height=\"41\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; color:black; font-size:12pt; text-align:right; vertical-align:middle; border-width:0.5pt; border-style:solid; border-color:black; background:white; width:97pt; height:30.75pt;\" align=\"right\" valign=\"middle\">4506904380</td><td width=\"132\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; color:black; font-size:12pt; text-align:right; vertical-align:middle; border-width:0.5pt; border-style:solid; border-color:black; background:white; width:99pt;\" align=\"right\" valign=\"middle\">10/5/2024</td><td width=\"102\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; color:black; font-size:12pt; vertical-align:middle; border-width:0.5pt; border-style:solid; border-color:black; background:rgb(147, 69, 17); width:77pt;\" align=\"general\" valign=\"middle\">Mohammad&nbsp;Babidan</td><td width=\"315\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; color:black; font-size:12pt; vertical-align:middle; border-width:0.5pt; border-style:solid; border-color:black; background:white; width:236pt;\" align=\"general\" valign=\"middle\">No response from end-user- project CRM is cancelled</td><td width=\"211\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; color:black; font-size:12pt; vertical-align:middle; border-width:0.5pt; border-style:solid; border-color:black; background:white; width:158pt;\" align=\"general\" valign=\"middle\">Ramlah Abdulmohsen</td><td width=\"177\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; color:black; font-size:11pt; font-weight:400; font-style:normal; font-family:&quot;Aptos Narrow&quot;, sans-serif; vertical-align:bottom; border-width:0.5pt; border-style:solid; border-color:black; width:133pt;\" align=\"general\" valign=\"bottom\">SDD Request sent on july 16</td></tr></tbody></table></div>",
                "add_time": "2024-07-16 07:57:52",
                "update_time": "2024-07-16 07:57:52",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-07-11 05:47:20",
            "data": {
                "id": 82596,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "12920883",
                "is_bulk_update_flag": null,
                "log_time": "2024-07-11 05:47:20",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Jay Mar",
                    "new_value_formatted": "Abdulrahman"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-07-10 12:58:34",
            "data": {
                "id": 82583,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "user_id",
                "old_value": "15523648",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-07-10 12:58:34",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Leena Nayef",
                    "new_value_formatted": "Jay Mar"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-07-07 10:31:24",
            "data": {
                "id": 32682,
                "user_id": 20601637,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" class=\"page_table\"><colgroup><col width=\"100\" style=\"width:75pt;\"><col width=\"110\" style=\"width:82pt;\"><col width=\"198\" style=\"width:149pt;\"><col width=\"548\" style=\"width:411pt;\"><col width=\"194\" style=\"width:145pt;\"><col width=\"245\" style=\"width:184pt;\"></colgroup><tbody><tr style=\"height:16.2pt;\"><td height=\"22\" width=\"100\" style=\"height:16.2pt; width:75pt; word-break:break-word; box-sizing:border-box; border-width:0px; border-color:gray;\" data-editing-info=\"{&quot;bgColorOverride&quot;:true,&quot;vAlignOverride&quot;:true}\">4506904380</td><td width=\"110\" style=\"width:82pt; border-width:0px; border-color:gray;\">10/5/2024</td><td width=\"198\" style=\"width:149pt; word-break:break-word; box-sizing:border-box; border-width:0px; border-color:gray;\" data-editing-info=\"{&quot;bgColorOverride&quot;:true}\">Mohammad&nbsp;Babidan</td><td width=\"548\" style=\"border-width:0px; border-left-style:none; border-color:gray; width:411pt; word-break:break-word; box-sizing:border-box;\" data-editing-info=\"{&quot;bgColorOverride&quot;:true}\">No response from end-user- project CRM is cancelled</td><td width=\"194\" style=\"border-width:0px; border-left-style:none; border-color:gray; width:145pt; word-break:break-word; box-sizing:border-box;\" data-editing-info=\"{&quot;bgColorOverride&quot;:true}\">Ramlah Abdulmohsen</td><td width=\"245\" style=\"width:184pt; border-width:0px; border-color:gray;\">SDD REQUEST ON JUNE 27</td></tr></tbody></table>",
                "add_time": "2024-07-07 10:31:24",
                "update_time": "2024-07-07 10:31:35",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "compliance@gyptech.com.sa",
                    "name": "Compliance",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_20601637_3075c75b9944f76834e4fad463251a43.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-07-02 11:15:55",
            "data": {
                "id": 32520,
                "user_id": 9392603,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "we had a meeting with Lead head designer Ramlah; send her the email confirming delivery; delivered the material at Aramco warehouse&nbsp;",
                "add_time": "2024-07-02 11:15:55",
                "update_time": "2024-07-02 11:15:55",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "arshadkamal@gyptech.com.sa",
                    "name": "Arshad Kamal",
                    "icon_url": null,
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-07-02 11:13:32",
            "data": {
                "id": 32516,
                "user_id": 9392603,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<div><br></div><div><a href=\"https://gyptech-568b5d.pipedrive.com/v1/files/170739/download\" data-pipecid=\"cid:170739\" rel=\"noopener noreferrer\"><img src=\"https://gyptech-568b5d.pipedrive.com/v1/files/170738/download\" data-pipecid=\"cid:170738\"></a><br></div>",
                "add_time": "2024-07-02 11:13:32",
                "update_time": "2024-07-02 11:17:18",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "arshadkamal@gyptech.com.sa",
                    "name": "Arshad Kamal",
                    "icon_url": null,
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-06-24 06:51:25",
            "data": {
                "id": 32307,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<div><table cellpadding=\"0\" cellspacing=\"0\" border=\"0\" class=\"page_table\"><colgroup><col width=\"530\" style=\"width:398pt;\"></colgroup><tbody><tr style=\"height:14.25pt;\"><td width=\"530\" height=\"19\" style=\"padding-top:1px; padding-right:1px; padding-left:1px; color:black; font-size:11pt; font-weight:400; font-style:normal; vertical-align:bottom; border-width:0.5pt; border-style:solid; border-color:windowtext; background:rgb(146, 208, 80); width:398pt; height:14.25pt;\" align=\"general\" valign=\"bottom\">For SDD Change - no yet changed</td></tr></tbody></table></div>",
                "add_time": "2024-06-24 06:51:25",
                "update_time": "2024-06-24 06:51:25",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-06-13 05:23:31",
            "data": {
                "id": 32217,
                "user_id": 13459159,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<p><b><u>4506904380 -</u></b><span>&nbsp;&nbsp;Status: No response from end-user</span></p>",
                "add_time": "2024-06-13 05:23:31",
                "update_time": "2024-06-13 05:23:31",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "jay@gyptech.com.sa",
                    "name": "Jay Mar",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_13459159_c7b68c293424dc3bc2ef1db8d1502147.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-05-27 12:27:07",
            "data": {
                "id": 31787,
                "user_id": 12920883,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/9392334\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"12920883:9392334\" data-mentions-you=\"false\" data-mentions-active=\"true\" data-mentions-permission=\"true\" rel=\"noopener noreferrer\" target=\"_blank\">@Faris alhashim</a>&nbsp;<a href=\"https://gyptech-568b5d.pipedrive.com/v1/files/169568/download\" data-pipecid=\"cid:169568\" rel=\"noopener noreferrer\"><img src=\"https://gyptech-568b5d.pipedrive.com/v1/files/169567/download\" data-pipecid=\"cid:169567\"></a>&nbsp;screenshot of P.O. status from the portal",
                "add_time": "2024-05-27 12:27:07",
                "update_time": "2024-05-27 12:27:07",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "abdulrahman@gyptech.com.sa",
                    "name": "Abdulrahman",
                    "icon_url": "https://usericons.pipedrive.com/profile_120x120_12920883_0dca7a5b3b9b00e44e718f54474418a5.jpg",
                    "is_you": false
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-05-27 07:10:30",
            "data": {
                "id": 31748,
                "user_id": 9392334,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "<a href=\"/users/details/15453699\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"9392334:15453699\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@hind battyour</a>&nbsp;<a href=\"/users/details/15523648\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"9392334:15523648\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@Leena Nayef</a>&nbsp; Whats the offical status of the PO in the system? Can you post a screen shot from the system here.&nbsp;",
                "add_time": "2024-05-27 07:10:30",
                "update_time": "2024-05-27 07:10:30",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "faris@gyptech.com.sa",
                    "name": "Faris alhashim",
                    "icon_url": null,
                    "is_you": false
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-05-02 03:44:16",
            "data": {
                "id": 80066,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "stage_change_time",
                "old_value": "2024-02-26 13:13:09",
                "new_value": "2024-05-02 03:44:16",
                "is_bulk_update_flag": null,
                "log_time": "2024-05-02 03:44:16",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-05-02 03:44:16",
            "data": {
                "id": 80065,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "stage_id",
                "old_value": "44",
                "new_value": "77",
                "is_bulk_update_flag": null,
                "log_time": "2024-05-02 03:44:16",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Awaiting Site Readiness"
                }
            }
        },
        {
            "object": "note",
            "timestamp": "2024-05-02 03:43:35",
            "data": {
                "id": 31237,
                "user_id": 15523648,
                "deal_id": 3769,
                "person_id": 7620,
                "org_id": 2220,
                "lead_id": null,
                "project_id": null,
                "content": "Material at warehouse but no response from Aramco&nbsp; <div><a href=\"/users/details/15453699\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"15523648:15453699\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@hind battyour</a>&nbsp;Any updates from your side?&nbsp;</div><div><br></div><div><a href=\"/users/details/13459159\" class=\"cui5-user-chip cui5-user-chip--variant-other\" data-mentions=\"15523648:13459159\" data-mentions-you=\"false\" data-mentions-active=\"false\" rel=\"noopener noreferrer\" target=\"_blank\">@Jay Mar</a>&nbsp;</div><div><br></div><div>SDD need to be changed.&nbsp;</div>",
                "add_time": "2024-05-02 03:43:35",
                "update_time": "2024-05-02 03:44:13",
                "active_flag": true,
                "pinned_to_deal_flag": false,
                "pinned_to_person_flag": false,
                "pinned_to_organization_flag": false,
                "pinned_to_lead_flag": false,
                "pinned_to_project_flag": false,
                "last_update_user_id": null,
                "organization": {
                    "name": "Saudi  Aramco"
                },
                "person": {
                    "name": "Babidan, Mohammad"
                },
                "deal": {
                    "title": "PO_4506904380 fantoni wood wall cladding / RFQ/728 ENGINEERING OFFICE bldg/ FLOOR 04/ LOBBY"
                },
                "lead": null,
                "user": {
                    "email": "leena.mohammed@gyptech.com.sa",
                    "name": "Leena Nayef",
                    "icon_url": null,
                    "is_you": false
                }
            }
        }
    ],
    "additional_data": {
        "filesCountByDay": {
            "2023-07-20": 1,
            "2022-12-11": 1,
            "2022-10-25": 5,
            "2022-09-20": 2,
            "2022-08-22": 5
        },
        "pagination": {
            "start": 0,
            "limit": 50,
            "more_items_in_collection": true,
            "next_start": 50
        }
    },
    "related_objects": {
        "person": {
            "7620": {
                "id": 7620,
                "name": "Babidan, Mohammad",
                "active_flag": true,
                "email": [
                    {
                        "value": "",
                        "primary": true
                    }
                ],
                "phone": [
                    {
                        "label": "work",
                        "value": "013 874-2044",
                        "primary": true
                    },
                    {
                        "label": "work",
                        "value": "0556300223",
                        "primary": false
                    }
                ]
            }
        }
    }
}

```

# Same call, but this time with dealChange

Api call :GET /v1/deals/3769/flow?start=0&all_changes=1&items=dealChange
This to show only deals stages change or changes on the deal itself, no other updates.

```json
{
    "success": true,
    "data": [
        {
            "object": "dealChange",
            "timestamp": "2025-11-10 12:44:25",
            "data": {
                "id": 100983,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "f71407beeb55195def1dce9326667e7c54f2cb42",
                "old_value": "85",
                "new_value": null,
                "is_bulk_update_flag": 1,
                "log_time": "2025-11-10 12:44:25",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "bulkAction",
                "origin_id": "5540587",
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:31:17",
            "data": {
                "id": 99966,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_change_time",
                "old_value": "2025-02-25 10:26:37",
                "new_value": "2025-09-14 11:31:17",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:31:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:31:17",
            "data": {
                "id": 99965,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_id",
                "old_value": "49",
                "new_value": "28",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:31:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Stuck/To be Canceled",
                    "new_value_formatted": "Approved"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-09-14 11:30:20",
            "data": {
                "id": 99964,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "9392603",
                "new_value": "9392643",
                "is_bulk_update_flag": null,
                "log_time": "2025-09-14 11:30:20",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Arshad Kamal",
                    "new_value_formatted": "Talha Waseem"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-06-15 12:33:13",
            "data": {
                "id": 96632,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "15453699",
                "new_value": "9392603",
                "is_bulk_update_flag": null,
                "log_time": "2025-06-15 12:33:13",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "origin": "app",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Arshad Kamal",
                    "old_value_formatted": "hind battyour"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-02-25 10:26:37",
            "data": {
                "id": 94593,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "stage_change_time",
                "old_value": "2024-10-22 12:48:44",
                "new_value": "2025-02-25 10:26:37",
                "is_bulk_update_flag": null,
                "log_time": "2025-02-25 10:26:37",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-02-25 10:26:37",
            "data": {
                "id": 94592,
                "item_id": 3769,
                "user_id": 9373337,
                "field_key": "stage_id",
                "old_value": "45",
                "new_value": "49",
                "is_bulk_update_flag": null,
                "log_time": "2025-02-25 10:26:37",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Everything Read but not started",
                    "new_value_formatted": "Stuck/To be Canceled"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2025-01-13 10:47:00",
            "data": {
                "id": 93905,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "f71407beeb55195def1dce9326667e7c54f2cb42",
                "old_value": null,
                "new_value": "85",
                "is_bulk_update_flag": null,
                "log_time": "2025-01-13 10:47:00",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-12 07:04:40",
            "data": {
                "id": 89367,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "56db4d96acbfa1e19d9d97c3821c3674d3fcaf94",
                "old_value": null,
                "new_value": "Multiple",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-12 07:04:40",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-12 06:28:53",
            "data": {
                "id": 89348,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "fdee83bde897e7e1477bb47e6d15bedb4272eb40",
                "old_value": null,
                "new_value": "474360",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-12 06:28:53",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-11 09:46:48",
            "data": {
                "id": 89137,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "3625266375cf115cf1a0edb6924d5c2c2243d540",
                "old_value": null,
                "new_value": "78",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-11 09:46:48",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-10 08:16:53",
            "data": {
                "id": 88917,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "4f2f060aaa56536fb78c5d1038ab56a24b8ebc63",
                "old_value": null,
                "new_value": "4506904380",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-10 08:16:53",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-10 08:16:50",
            "data": {
                "id": 88916,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "5ffea68859bd7089ce52f603ee5f88c14b3ff260",
                "old_value": null,
                "new_value": "DHAHRAN",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-10 08:16:50",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-06 09:57:57",
            "data": {
                "id": 88656,
                "item_id": 3769,
                "user_id": 20601637,
                "field_key": "bd7bb3b2758ca81feebf015ca60bf528eafe47f0",
                "old_value": null,
                "new_value": "9850",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-06 09:57:57",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "RAMLAH"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-11-03 06:43:50",
            "data": {
                "id": 88425,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "15453699",
                "is_bulk_update_flag": null,
                "log_time": "2024-11-03 06:43:50",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Jay Mar",
                    "new_value_formatted": "hind battyour"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-10-22 12:48:44",
            "data": {
                "id": 87564,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_change_time",
                "old_value": "2024-05-02 03:44:16",
                "new_value": "2024-10-22 12:48:44",
                "is_bulk_update_flag": null,
                "log_time": "2024-10-22 12:48:44",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-10-22 12:48:44",
            "data": {
                "id": 87563,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "stage_id",
                "old_value": "77",
                "new_value": "45",
                "is_bulk_update_flag": null,
                "log_time": "2024-10-22 12:48:44",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Everything Read but not started"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-22 07:55:22",
            "data": {
                "id": 85602,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "9392603",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-22 07:55:22",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Arshad Kamal",
                    "new_value_formatted": "Jay Mar"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-22 07:55:07",
            "data": {
                "id": 85601,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "9392603",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-22 07:55:07",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Arshad Kamal",
                    "old_value_formatted": "Jay Mar"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-08-18 10:57:31",
            "data": {
                "id": 85412,
                "item_id": 3769,
                "user_id": 9392603,
                "field_key": "user_id",
                "old_value": "12920883",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-08-18 10:57:31",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Jay Mar",
                    "old_value_formatted": "Abdulrahman"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-07-11 05:47:20",
            "data": {
                "id": 82596,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "13459159",
                "new_value": "12920883",
                "is_bulk_update_flag": null,
                "log_time": "2024-07-11 05:47:20",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Jay Mar",
                    "new_value_formatted": "Abdulrahman"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-07-10 12:58:34",
            "data": {
                "id": 82583,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "user_id",
                "old_value": "15523648",
                "new_value": "13459159",
                "is_bulk_update_flag": null,
                "log_time": "2024-07-10 12:58:34",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Leena Nayef",
                    "new_value_formatted": "Jay Mar"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-05-02 03:44:16",
            "data": {
                "id": 80066,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "stage_change_time",
                "old_value": "2024-02-26 13:13:09",
                "new_value": "2024-05-02 03:44:16",
                "is_bulk_update_flag": null,
                "log_time": "2024-05-02 03:44:16",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-05-02 03:44:16",
            "data": {
                "id": 80065,
                "item_id": 3769,
                "user_id": 15523648,
                "field_key": "stage_id",
                "old_value": "44",
                "new_value": "77",
                "is_bulk_update_flag": null,
                "log_time": "2024-05-02 03:44:16",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Awaiting Site Readiness"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-04-07 08:59:29",
            "data": {
                "id": 79507,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "16341599",
                "new_value": "15523648",
                "is_bulk_update_flag": null,
                "log_time": "2024-04-07 08:59:29",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Lujain Ali",
                    "new_value_formatted": "Leena Nayef"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-02-26 13:13:09",
            "data": {
                "id": 78351,
                "item_id": 3769,
                "user_id": 9392334,
                "field_key": "stage_change_time",
                "old_value": "2023-01-29 08:35:48",
                "new_value": "2024-02-26 13:13:09",
                "is_bulk_update_flag": null,
                "log_time": "2024-02-26 13:13:09",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 08:06:13",
            "data": {
                "id": 76134,
                "item_id": 3769,
                "user_id": 15453699,
                "field_key": "won_time",
                "old_value": "2024-01-08 07:58:14",
                "new_value": null,
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 08:06:13",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 08:06:13",
            "data": {
                "id": 76133,
                "item_id": 3769,
                "user_id": 15453699,
                "field_key": "close_time",
                "old_value": "2024-01-08 07:58:14",
                "new_value": null,
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 08:06:13",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 08:06:13",
            "data": {
                "id": 76132,
                "item_id": 3769,
                "user_id": 15453699,
                "field_key": "status",
                "old_value": "won",
                "new_value": "open",
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 08:06:13",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 07:58:14",
            "data": {
                "id": 76131,
                "item_id": 3769,
                "user_id": 16341599,
                "field_key": "won_time",
                "old_value": null,
                "new_value": "2024-01-08 07:58:14",
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 07:58:14",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 07:58:14",
            "data": {
                "id": 76130,
                "item_id": 3769,
                "user_id": 16341599,
                "field_key": "close_time",
                "old_value": null,
                "new_value": "2024-01-08 07:58:14",
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 07:58:14",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2024-01-08 07:58:14",
            "data": {
                "id": 76129,
                "item_id": 3769,
                "user_id": 16341599,
                "field_key": "status",
                "old_value": "open",
                "new_value": "won",
                "is_bulk_update_flag": null,
                "log_time": "2024-01-08 07:58:14",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-11-21 06:16:03",
            "data": {
                "id": 74241,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "14756895",
                "new_value": "16341599",
                "is_bulk_update_flag": null,
                "log_time": "2023-11-21 06:16:03",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Rabiyah",
                    "new_value_formatted": "Lujain Ali"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-08-27 07:44:43",
            "data": {
                "id": 70895,
                "item_id": 3769,
                "user_id": 15453699,
                "field_key": "aaff5efec614d2cd18aecdfa5f800af9167cac1d",
                "old_value": "2023-04-23",
                "new_value": "2023-10-29",
                "is_bulk_update_flag": null,
                "log_time": "2023-08-27 07:44:43",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-08-22 07:20:09",
            "data": {
                "id": 70495,
                "item_id": 3769,
                "user_id": 13459159,
                "field_key": "user_id",
                "old_value": "12728812",
                "new_value": "14756895",
                "is_bulk_update_flag": null,
                "log_time": "2023-08-22 07:20:09",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Amal ALkhaldi",
                    "new_value_formatted": "Rabiyah"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-02-15 08:27:43",
            "data": {
                "id": 64788,
                "item_id": 3769,
                "user_id": 15453699,
                "field_key": "aaff5efec614d2cd18aecdfa5f800af9167cac1d",
                "old_value": "2023-02-23",
                "new_value": "2023-04-23",
                "is_bulk_update_flag": null,
                "log_time": "2023-02-15 08:27:43",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-29 08:35:48",
            "data": {
                "id": 64294,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_change_time",
                "old_value": "2023-01-29 08:35:32",
                "new_value": "2023-01-29 08:35:48",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-29 08:35:48",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-29 08:35:48",
            "data": {
                "id": 64293,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_id",
                "old_value": "29",
                "new_value": "44",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-29 08:35:48",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Awaiting Payment",
                    "new_value_formatted": "Awaiting Site Readiness"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-29 08:35:32",
            "data": {
                "id": 64292,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_change_time",
                "old_value": "2023-01-26 11:36:04",
                "new_value": "2023-01-29 08:35:32",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-29 08:35:32",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-29 08:35:32",
            "data": {
                "id": 64291,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_id",
                "old_value": "44",
                "new_value": "29",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-29 08:35:32",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "new_value_formatted": "Awaiting Payment",
                    "old_value_formatted": "Awaiting Site Readiness"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-26 11:36:04",
            "data": {
                "id": 64273,
                "item_id": 3769,
                "user_id": 9392603,
                "field_key": "stage_change_time",
                "old_value": "2023-01-26 07:04:17",
                "new_value": "2023-01-26 11:36:04",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-26 11:36:04",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-26 11:36:04",
            "data": {
                "id": 64272,
                "item_id": 3769,
                "user_id": 9392603,
                "field_key": "stage_id",
                "old_value": "29",
                "new_value": "44",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-26 11:36:04",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Awaiting Payment",
                    "new_value_formatted": "Awaiting Site Readiness"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-26 07:04:17",
            "data": {
                "id": 64263,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_change_time",
                "old_value": "2022-09-20 04:58:38",
                "new_value": "2023-01-26 07:04:17",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-26 07:04:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2023-01-26 07:04:17",
            "data": {
                "id": 64262,
                "item_id": 3769,
                "user_id": 12728812,
                "field_key": "stage_id",
                "old_value": "27",
                "new_value": "29",
                "is_bulk_update_flag": null,
                "log_time": "2023-01-26 07:04:17",
                "change_source": "app",
                "change_source_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "origin": "",
                "origin_id": null,
                "additional_data": {
                    "old_value_formatted": "Order Received",
                    "new_value_formatted": "Awaiting Payment"
                }
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-28 12:15:44",
            "data": {
                "id": 63345,
                "item_id": 3769,
                "user_id": 15733715,
                "field_key": "visible_to",
                "old_value": "1",
                "new_value": "3",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-28 12:15:44",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-28 06:45:48",
            "data": {
                "id": 61978,
                "item_id": 3769,
                "user_id": 15733715,
                "field_key": "visible_to",
                "old_value": "3",
                "new_value": "1",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-28 06:45:48",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-27 09:06:28",
            "data": {
                "id": 55328,
                "item_id": 3769,
                "user_id": 15733715,
                "field_key": "visible_to",
                "old_value": "1",
                "new_value": "3",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-27 09:06:28",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-27 08:36:37",
            "data": {
                "id": 51641,
                "item_id": 3769,
                "user_id": 9392334,
                "field_key": "visible_to",
                "old_value": "3",
                "new_value": "1",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-27 08:36:37",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-26 11:52:49",
            "data": {
                "id": 47788,
                "item_id": 3769,
                "user_id": 15733715,
                "field_key": "visible_to",
                "old_value": "1",
                "new_value": "3",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-26 11:52:49",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        },
        {
            "object": "dealChange",
            "timestamp": "2022-12-26 11:09:01",
            "data": {
                "id": 43717,
                "item_id": 3769,
                "user_id": 9392334,
                "field_key": "visible_to",
                "old_value": "3",
                "new_value": "1",
                "is_bulk_update_flag": 1,
                "log_time": "2022-12-26 11:09:01",
                "change_source": "api",
                "change_source_user_agent": "bulk-actions-api",
                "origin": "",
                "origin_id": null,
                "additional_data": []
            }
        }
    ],
    "additional_data": {
        "filesCountByDay": [],
        "pagination": {
            "start": 0,
            "limit": 50,
            "more_items_in_collection": true,
            "next_start": 50
        }
    }
}
```


