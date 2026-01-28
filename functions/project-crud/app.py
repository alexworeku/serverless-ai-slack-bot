import json
import os
import boto3
from datetime import datetime
from typing import Any

from infrastructure.dynamo_project_repository import (
    DynamoProjectRepository,
    ProjectWriteError,
    ProjectReadError,
    ProjectDeleteError,
)
from models.project_model import ProjectModel, ProjectStatus

dynamodb = boto3.resource("dynamodb")

repo = DynamoProjectRepository(
    dyn_resource=dynamodb,
    projects_table_name=os.environ["PROJ_TABLE_NAME"],
    project_channel_table_name=os.environ["PROJCHANNEL_TABLE_NAME"],
    proj_ch_index_name=os.environ["PROJCHANNEL_GSI_NAME"],
)

def response(status: int, body: Any):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def parse_body(event) -> dict:
    if not event.get("body"):
        return {}
    return json.loads(event["body"])


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["requestContext"]["http"]["path"]
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    try:
        if method == "POST" and path == "/projects":
            body = parse_body(event)

            project = ProjectModel(
                project_id=body["project_id"],
                api_token=body["api_token"],
                api_url=body["api_url"],
                project_owner_email=body["project_owner_email"],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            channel_id = body["channel_id"]

            repo.upsert_project_with_channel(project, channel_id)

            return response(201, {"message": "Project created"})


        if method == "GET" and path == "/projects":
            limit = int(query_params.get("limit", 25))
            last_key = query_params.get("last_key")

            projects, next_key = repo.list_projects(
                limit=limit,
                last_evaluated_key=json.loads(last_key) if last_key else None,
            )

            return response(
                200,
                {
                    "items": [p.model_dump() for p in projects],
                    "last_evaluated_key": next_key,
                },
            )
            
        if (
            method == "GET"
            and "project_id" in path_params
            and path.endswith("/channels")
        ):
            project_id = path_params["project_id"]
            channels = repo.get_channels_by_project(project_id)

            return response(
                200,
                [c.model_dump() for c in channels],
            )

        # if (
        #     method == "GET"
        #     and "channel_id" in path_params
        #     and path.startswith("/channels/")
        # ):
        #     channel_id = path_params["channel_id"]
        #     projects = repo.get_projects_by_channel(channel_id)

        #     return response(
        #         200,
        #         [p.model_dump() for p in projects],
        #     )

        if method == "DELETE" and "project_id" in path_params:
            project_id = path_params["project_id"]

            repo.delete_project_completely(project_id)

            return response(200, {"deleted": True})

        return response(404, {"message": "Not Found"})

    except (ProjectWriteError, ProjectReadError, ProjectDeleteError) as e:
        return response(500, {"error": str(e)})

    except KeyError as e:
        return response(400, {"error": f"Missing field {str(e)}"})

    except Exception as e:
        return response(500, {"error": "Internal server error"})
