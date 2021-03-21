# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import logging
import os
import sys
import urllib.request

LAMBDA_AGENT_NAME_HEADER_KEY = "Lambda-Extension-Name"
LAMBDA_AGENT_IDENTIFIER_HEADER_KEY = "Lambda-Extension-Identifier"

class ExtensionsAPIClient():
    def __init__(self):
        try:
            self.logger = self.get_logger()
            runtime_api_address = os.environ['AWS_LAMBDA_RUNTIME_API']
            self.runtime_api_base_url = f"http://{runtime_api_address}/2020-01-01/extension"
        except Exception as e:
            raise Exception(f"AWS_LAMBDA_RUNTIME_API is not set {e}") from e

    # Register as early as possible - the runtime initialization starts after all extensions have registered.
    def register(self, agent_unique_name, registration_body):
        try:
            self.logger.debug(f"Registering to ExtensionsAPIClient on {self.runtime_api_base_url}")
            req = urllib.request.Request(f"{self.runtime_api_base_url}/register")
            req.method = 'POST'
            req.add_header(LAMBDA_AGENT_NAME_HEADER_KEY, agent_unique_name)
            req.add_header("Content-Type", "application/json")
            data = json.dumps(registration_body).encode("utf-8")
            req.data = data
            resp = urllib.request.urlopen(req)
            if resp.status != 200:
                self.logger.error(f"/register request to ExtensionsAPIClient failed. Status:  {resp.status}, Response: {resp.read()}")
                # Fail the extension
                sys.exit(1)
            agent_identifier = resp.headers.get(LAMBDA_AGENT_IDENTIFIER_HEADER_KEY)
            return agent_identifier
        except Exception as e:
            raise Exception(f"Failed to register to ExtensionsAPIClient: on {self.runtime_api_base_url}/register \
                with agent_unique_name:{agent_unique_name}  \
                and registration_body:{registration_body}\nError: {e}") from e

    # Call the following method when the extension is ready to receive the next invocation
    # and there is no job it needs to execute beforehand.
    def next(self, agent_id):
        try:
            req = urllib.request.Request(f"{self.runtime_api_base_url}/event/next")
            req.method = 'GET'
            req.add_header(LAMBDA_AGENT_IDENTIFIER_HEADER_KEY, agent_id)
            req.add_header("Content-Type", "application/json")
            resp = urllib.request.urlopen(req)
            if resp.status != 200:
                self.logger.error(f"/event/next request to ExtensionsAPIClient failed. Status: {resp.status}, Response: {resp.read()} ")
                # Fail the extension
                sys.exit(1)
            data = resp.read()
            self.logger.info(f"Received response from ExtensionsAPIClient: {data}")
            return data
        except Exception as e:
            raise Exception(f"Failed to get /event/next from ExtensionsAPIClient: {e}") from e

    def get_logger(self):
        log_level = os.getenv("LOGS_EXT_LOG_LEVEL", "INFO").upper()
        # validate entered value, fallback to INFO
        if log_level not in ["DEBUG", "INFO", "WARNING", "WARNING", "ERROR", "CRITICAL"]:
            log_level = "INFO"
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.getLevelName(log_level))
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(module)s %(thread)d %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
