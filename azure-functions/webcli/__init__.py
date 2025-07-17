import logging
import json
import os
import asyncio
import requests
from azure.functions import HttpRequest, HttpResponse
from azure.identity import DefaultAzureCredential
import time

# Configuration from environment variables
RESOURCE_GROUP = os.environ.get('AZURE_RESOURCE_GROUP', 'gentik-pipelines')
CONTAINER_NAME = os.environ.get('AZURE_CONTAINER_NAME', 'tiktok-pipeline')
CONTAINER_API_URL = os.environ.get('CONTAINER_API_URL', 'http://20.171.201.193:8000')
ACCESS_CODE = os.environ.get('WEBCLI_ACCESS_CODE', 'tiktok-secure-2025')
SUBSCRIPTION_ID = os.environ.get('AZURE_SUBSCRIPTION_ID', '')

# Azure credentials for secure service-to-service communication
credential = DefaultAzureCredential()

def main(req: HttpRequest) -> HttpResponse:
    logging.info('WebCLI function processed a request.')
    
    # Handle CORS preflight
    if req.method == 'OPTIONS':
        return HttpResponse(
            status_code=200,
            headers={
                'Access-Control-Allow-Origin': 'https://white-dune-06252521e.2.azurestaticapps.net',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                'Access-Control-Max-Age': '86400'
            }
        )
    
    # Security headers for all responses
    security_headers = {
        'Access-Control-Allow-Origin': 'https://white-dune-06252521e.2.azurestaticapps.net',
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }
    
    try:
        # Get access token from query or body
        token = req.params.get('token')
        if not token and req.method == 'POST':
            try:
                req_body = req.get_json()
                token = req_body.get('token') if req_body else None
            except:
                pass
        
        # Validate access code
        if not token or token != ACCESS_CODE:
            logging.warning(f"Invalid access attempt with token: {token}")
            return HttpResponse(
                json.dumps({"error": "Invalid access code", "authenticated": False}),
                status_code=401,
                headers=security_headers
            )
        
        # Get command from request
        command = req.params.get('cmd', 'echo "Connected to TikTok Pipeline"')
        if req.method == 'POST':
            try:
                req_body = req.get_json()
                command = req_body.get('command', command) if req_body else command
            except:
                pass
        
        # Log the command for security auditing
        logging.info(f"Executing command: {command[:50]}...")
        
        # Execute command via container API or CLI depending on command type
        # Execute ALL commands via Azure CLI exec for full terminal access
        result = execute_via_azure_cli(command)        
        return HttpResponse(
            json.dumps({
                "output": result.get('output', ''),
                "error": result.get('error', ''),
                "exit_code": result.get('exit_code', 0),
                "command": command,
                "timestamp": time.time(),
                "authenticated": True
            }),
            status_code=200,
            headers=security_headers
        )
        
    except Exception as e:
        logging.error(f"Error in webcli function: {str(e)}")
        return HttpResponse(
            json.dumps({
                "error": "Internal server error", 
                "authenticated": True,
                "timestamp": time.time()
            }),
            status_code=500,
            headers=security_headers
        )

def execute_via_container_api(command):
    """Execute pipeline commands via the container's HTTP API."""
    try:
        # Parse pipeline CLI commands and convert to API calls
        if 'stats' in command:
            response = requests.get(f"{CONTAINER_API_URL}/stats", timeout=10)
            return {
                'output': response.text,
                'error': '',
                'exit_code': 0 if response.status_code == 200 else response.status_code
            }
        elif 'health' in command:
            response = requests.get(f"{CONTAINER_API_URL}/health", timeout=10)
            return {
                'output': response.text,
                'error': '',
                'exit_code': 0 if response.status_code == 200 else response.status_code
            }
        elif 'jobs' in command:
            response = requests.get(f"{CONTAINER_API_URL}/jobs", timeout=10)
            return {
                'output': response.text,
                'error': '',
                'exit_code': 0 if response.status_code == 200 else response.status_code
            }
        elif command.startswith('curl http'):
            # Extract URL from curl command
            url_start = command.find('http')
            if url_start != -1:
                url = command[url_start:].split()[0]
                response = requests.get(url, timeout=10)
                return {
                    'output': response.text,
                    'error': '',
                    'exit_code': 0 if response.status_code == 200 else response.status_code
                }
        
        # For other CLI commands, fall back to Azure CLI exec
        return execute_via_azure_cli(command)
        
    except requests.RequestException as e:
        return {
            'output': '',
            'error': f'API request failed: {str(e)}',
            'exit_code': 1
        }
    except Exception as e:
        return {
            'output': '',
            'error': f'Command execution failed: {str(e)}',
            'exit_code': 1
        }

def execute_via_azure_cli(command):
    """Execute command in Azure Container Instance using Azure CLI with managed identity."""
    try:
        import subprocess
        
        # Use Azure CLI with managed identity for secure access
        az_command = [
            'az', 'container', 'exec',
            '--resource-group', RESOURCE_GROUP,
            '--name', CONTAINER_NAME,
            '--exec-command', command
        ]
        
        # Execute with timeout and managed identity
        result = subprocess.run(
            az_command,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'AZURE_CORE_USE_CLI_IDENTITY': 'true'}
        )
        
        return {
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'output': '',
            'error': 'Command timed out after 30 seconds',
            'exit_code': 124
        }
    except Exception as e:
        return {
            'output': '',
            'error': f'Failed to execute command: {str(e)}',
            'exit_code': 1
        } 