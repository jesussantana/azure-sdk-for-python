# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

import os


class SampleRepositoryActions(object):

    base_url = os.environ.get("ACR_BASE_URL")

    def view_repositories(self):
        client = ContainerRegistryClient(self.base_url, DefaultAzureCredential())

        repositories = client.list_repositories()

        for idx, repo in enumerate(repositories):
            print("Repository #{}: {}".format(idx, repo))

    def get_repository_metadata(self):
        client = ContainerRegistryClient(self.base_url, DefaultAzureCredential())

        repo_client = client.get_repository_client("hello-world")

        attributes = repo_client.get_attributes()

        print(attributes.name)
        print(attributes.registry)
        print(attributes.created_time)
        print(attributes.last_updated_time)
        print(attributes.manifest_count)
        print(attributes.tag_count)
        print(attributes.permission.can_list)
        print(attributes.permission.can_read)
        print(attributes.permission.can_write)
        print(attributes.permission.can_delete)

    def set_repository_permissions(self):
        client = ContainerRegistryClient(self.base_url, DefaultAzureCredential())

        repo_client = client.get_repository_client("hello-world")

        permissions = ContentPermissions(list=true, read=true, write=true, delete=false)

        repo_client.set_permissions(permissions)

    def delete_repository(self):
        client = ContainerRegistryClient(self.base_url, DefaultAzureCredential())

        result = client.delete_repository("hello-world")

        for manifest in result.manifests_deleted:
            print("Deleted {}".format(manifest))

        for tag in result.tags_deleted:
            print("Deleted tags {}".format(tag))
