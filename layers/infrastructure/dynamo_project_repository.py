from typing import List, Tuple, Optional
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from models.project_model import ProjectModel
from models.project_channel_model import ProjectChannelModel
from boto3.dynamodb.types import TypeSerializer

class RepositoryError(Exception):
    """Base repository exception."""


class ProjectWriteError(RepositoryError):
    pass


class ProjectReadError(RepositoryError):
    pass


class ProjectDeleteError(RepositoryError):
    pass

class DynamoProjectRepository:
    """
    DynamoDB-backed repository for Project and ProjectChannel entities.

    Tables:
      - Projects (PK: project_id)
      - ProjectChannel (PK: channel_id, SK: project_id)
        - GSI: project_id (PK), channel_id (SK)
    """

    def __init__(
        self,
        dyn_resource: boto3.resources.base.ServiceResource,
        projects_table_name: str,
        project_channel_table_name: str,
        proj_ch_index_name: str,
    ):
        self.dyn_resource = dyn_resource
        self.client = dyn_resource.meta.client

        self.projects_table_name = projects_table_name
        self.project_channel_table_name = project_channel_table_name
        self.proj_ch_index_name = proj_ch_index_name

        self.projects_table = dyn_resource.Table(projects_table_name)
        self.project_channel_table = dyn_resource.Table(project_channel_table_name)
   
    

    def _serialize(self, item: dict) -> dict:
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in item.items()}  
    
    def upsert_project_with_channel(
        self,
        project: ProjectModel,
        channel_id: str,
    ) -> None:
        """
        Atomically:
          - Upsert project
          - Link project to channel
        """
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.projects_table_name,
                            "Item": self._serialize(project.model_dump(mode="json")),
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.project_channel_table_name,
                            "Item": {
                                "channel_id": {"S": channel_id},
                                "project_id": {"S": project.project_id},
                            },
                        }
                    },
                ]
            )
        except ClientError as e:
            raise ProjectWriteError(
                f"Failed to upsert project {project.project_id}"
            ) from e

    def link_project_to_channels(
        self,
        project_channels: List[ProjectChannelModel],
    ) -> None:
        try:
            with self.project_channel_table.batch_writer() as batch:
                for proj_ch in project_channels:
                    batch.put_item(Item=proj_ch.model_dump(mode="json"))
        except ClientError as e:
            raise ProjectWriteError(
                "Failed to link project to channels"
            ) from e

    def unlink_project_from_channels(
        self,
        project_channels: List[ProjectChannelModel],
    ) -> None:
        try:
            with self.project_channel_table.batch_writer() as batch:
                for proj_ch in project_channels:
                    batch.delete_item(
                        Key={
                            "channel_id": proj_ch.channel_id,
                            "project_id": proj_ch.project_id,
                        }
                    )
        except ClientError as e:
            raise ProjectDeleteError(
                "Failed to unlink project from channels"
            ) from e

    def delete_project_completely(self, project_id: str) -> None:
        """
        Deletes:
          - all channel links
          - the project record
        """
        try:
            channels = self.get_channels_by_project(project_id)

            if channels:
                self.unlink_project_from_channels(channels)

            self.projects_table.delete_item(
                Key={"project_id": project_id}
            )
        except ClientError as e:
            raise ProjectDeleteError(
                f"Failed to delete project {project_id}"
            ) from e

  
    def get_projects_by_channel(
        self,
        channel_id: str,
    ) -> List[ProjectModel]:
        try:
            response = self.project_channel_table.query(
                KeyConditionExpression=Key("channel_id").eq(channel_id)
            )

            mappings = response.get("Items", [])
            if not mappings:
                return []

            keys = [{"project_id": m["project_id"]} for m in mappings]

            result = self.client.batch_get_item(
                RequestItems={
                    self.projects_table_name: {
                        "Keys": keys,
                        "ConsistentRead": False,
                    }
                }
            )

            items = result.get("Responses", {}).get(
                self.projects_table_name, []
            )

            return [ProjectModel(**item) for item in items]

        except ClientError as e:
            raise ProjectReadError(
                f"Failed to get projects for channel {channel_id}"
            ) from e

    def get_channels_by_project(
        self,
        project_id: str,
    ) -> List[ProjectChannelModel]:
        try:
            response = self.project_channel_table.query(
                IndexName=self.proj_ch_index_name,
                KeyConditionExpression=Key("project_id").eq(project_id),
            )

            return [
                ProjectChannelModel(**item)
                for item in response.get("Items", [])
            ]

        except ClientError as e:
            raise ProjectReadError(
                f"Failed to get channels for project {project_id}"
            ) from e

    def list_projects(
        self,
        limit: int = 25,
        last_evaluated_key: Optional[dict] = None,
    ) -> Tuple[List[ProjectModel], Optional[dict]]:
        try:
            params = {"Limit": limit}
            if last_evaluated_key:
                params["ExclusiveStartKey"] = last_evaluated_key

            response = self.projects_table.scan(**params)

            projects = [
                ProjectModel(**item)
                for item in response.get("Items", [])
            ]

            return projects, response.get("LastEvaluatedKey")

        except ClientError as e:
            raise ProjectReadError(f"Failed to list projects: {e}",) from e
