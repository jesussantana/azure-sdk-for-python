# coding=utf-8
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
FILE: sample_translation_with_azure_blob_async.py

DESCRIPTION:
    This sample demonstrates how to use Azure Blob Storage to set up the necessary resources to create a translation
    job. Run the sample to create containers, upload documents, and generate SAS tokens for the source/target
    containers. Once the job is completed, use the storage library to download your documents locally.

PREREQUISITE:
    This sample requires you install azure-storage-blob client library:
    https://pypi.org/project/azure-storage-blob/

USAGE:
    python sample_translation_with_azure_blob_async.py

    Set the environment variables with your own values before running the sample:
    1) AZURE_DOCUMENT_TRANSLATION_ENDPOINT - the endpoint to your Document Translation resource.
    2) AZURE_DOCUMENT_TRANSLATION_KEY - your Document Translation API key.
    3) AZURE_STORAGE_SOURCE_ENDPOINT - the endpoint to your Storage account
    4) AZURE_STORAGE_ACCOUNT_NAME - the name of your storage account
    5) AZURE_STORAGE_SOURCE_KEY - the shared access key to your storage account

    Optional environment variables - if not set, they will be created for you
    6) AZURE_STORAGE_SOURCE_CONTAINER_NAME - the name of your source container
    7) AZURE_STORAGE_TARGET_CONTAINER_NAME - the name of your target container
    8) AZURE_DOCUMENT_NAME - the name and file extension of your document in this directory
        e.g. "mydocument.txt"
"""

import os
import datetime
import asyncio
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError
from azure.ai.documenttranslation.aio import DocumentTranslationClient
from azure.ai.documenttranslation import (
    DocumentTranslationInput,
    TranslationTarget
)
from azure.storage.blob.aio import BlobServiceClient, BlobClient
from azure.storage.blob import generate_container_sas


class SampleTranslationWithAzureBlobAsync(object):

    def __init__(self):
        self.endpoint = os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"]
        self.key = os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"]
        self.storage_endpoint = os.environ["AZURE_STORAGE_SOURCE_ENDPOINT"]
        self.storage_account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
        self.storage_key = os.environ["AZURE_STORAGE_SOURCE_KEY"]
        self.storage_source_container_name = os.getenv("AZURE_STORAGE_SOURCE_CONTAINER_NAME", None)  # Optional
        self.storage_target_container_name = os.getenv("AZURE_STORAGE_TARGET_CONTAINER_NAME", None)  # Optional
        self.document_name = os.getenv("AZURE_DOCUMENT_NAME", None)  # Optional document in same directory as this sample

    async def sample_translation_with_azure_blob(self):

        translation_client = DocumentTranslationClient(
            self.endpoint, AzureKeyCredential(self.key)
        )

        blob_service_client = BlobServiceClient(
            self.storage_endpoint,
            credential=self.storage_key
        )

        source_container = await self.create_container(
            blob_service_client,
            container_name=self.storage_source_container_name or "translation-source-container",
        )
        target_container = await self.create_container(
            blob_service_client,
            container_name=self.storage_target_container_name or "translation-target-container"
        )

        if self.document_name:
            with open(self.document_name, "rb") as doc:
                await source_container.upload_blob(self.document_name, doc)
        else:
            self.document_name = "example_document.txt"
            await source_container.upload_blob(
                name=self.document_name,
                data=b"This is an example translation with the document translation client library"
            )
        print("Uploaded document {} to storage container {}".format(self.document_name, source_container.container_name))

        source_container_sas_url = self.generate_sas_url(source_container, permissions="rl")
        target_container_sas_url = self.generate_sas_url(target_container, permissions="wl")

        translation_inputs = [
            DocumentTranslationInput(
                source_url=source_container_sas_url,
                targets=[
                    TranslationTarget(
                        target_url=target_container_sas_url,
                        language_code="fr"
                    )
                ]
            )
        ]

        job = await translation_client.create_translation_job(translation_inputs)
        print("Created translation job with ID: {}".format(job.id))
        print("Waiting until job completes...")

        job_result = await translation_client.wait_until_done(job.id)
        print("Job status: {}".format(job_result.status))

        doc_results = translation_client.list_all_document_statuses(job_result.id)

        print("\nDocument results:")
        async for document in doc_results:
            print("Document ID: {}".format(document.id))
            print("Document status: {}".format(document.status))
            if document.status == "Succeeded":
                print("Document location: {}".format(document.translated_document_url))
                print("Translated to language: {}\n".format(document.translate_to))

                blob_client = BlobClient.from_blob_url(document.translated_document_url, credential=self.storage_key)
                async with blob_client:
                    with open("translated_"+self.document_name, "wb") as my_blob:
                        download_stream = await blob_client.download_blob()
                        my_blob.write(await download_stream.readall())

                print("Downloaded {} locally".format("translated_"+self.document_name))
            else:
                print("\nThere was a problem translating your document.")
                print("Document Error Code: {}, Message: {}\n".format(document.error.code, document.error.message))

        await translation_client.close()
        await blob_service_client.close()

    async def create_container(self, blob_service_client, container_name):
        try:
            container_client = await blob_service_client.create_container(container_name)
            print("Creating container: {}".format(container_name))
        except ResourceExistsError:
            print("The container with name {} already exists".format(container_name))
            container_client = blob_service_client.get_container_client(container=container_name)
        return container_client

    def generate_sas_url(self, container, permissions):
        sas_token = generate_container_sas(
            account_name=self.storage_account_name,
            container_name=container.container_name,
            account_key=self.storage_key,
            permission=permissions,
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )

        container_sas_url = self.storage_endpoint + container.container_name + "?" + sas_token
        print("Generating {} SAS URL".format(container.container_name))
        return container_sas_url


async def main():
    sample = SampleTranslationWithAzureBlobAsync()
    await sample.sample_translation_with_azure_blob()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
