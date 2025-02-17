from typing import List, Dict, Any
import asyncio
import os
import yaml
import platform
from mcp.types import TextContent, Tool, Prompt, PromptArgument, GetPromptResult, PromptMessage
from .podman_executor import PodmanComposeExecutor, PodmanContainerExecutor


async def parse_port_mapping(host_key: str, container_port: str | int) -> tuple[str, str] | tuple[str, str, str]:
    if '/' in str(host_key):
        host_port, protocol = host_key.split('/')
        if protocol.lower() == 'udp':
            return (str(host_port), str(container_port), 'udp')
        return (str(host_port), str(container_port))

    if isinstance(container_port, str) and '/' in container_port:
        port, protocol = container_port.split('/')
        if protocol.lower() == 'udp':
            return (str(host_key), port, 'udp')
        return (str(host_key), port)

    return (str(host_key), str(container_port))


class PodmanHandlers:
    TIMEOUT_AMOUNT = 200

    @staticmethod
    async def handle_create_container(arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            image = arguments["image"]
            container_name = arguments.get("name")
            ports = arguments.get("ports", {})
            environment = arguments.get("environment", {})

            if not image:
                raise ValueError("Image name cannot be empty")

            executor = PodmanContainerExecutor()
            code, out, err = await executor.run(image, container_name, ports, environment)

            if code != 0:
                raise Exception(f"Failed to create container: {err}")

            return [TextContent(type="text", text=f"Created container '{container_name}'\nOutput: {out}")]
        except asyncio.TimeoutError:
            return [TextContent(type="text", text=f"Operation timed out after {PodmanHandlers.TIMEOUT_AMOUNT} seconds")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating container: {str(e)} | Arguments: {arguments}")]

    @staticmethod
    async def handle_deploy_compose(arguments: Dict[str, Any]) -> List[TextContent]:
        debug_info = []
        try:
            compose_yaml = arguments.get("compose_yaml")
            project_name = arguments.get("project_name")

            if not compose_yaml or not project_name:
                raise ValueError(
                    "Missing required compose_yaml or project_name")

            yaml_content = PodmanHandlers._process_yaml(
                compose_yaml, debug_info)
            compose_path = PodmanHandlers._save_compose_file(
                yaml_content, project_name)

            try:
                result = await PodmanHandlers._deploy_stack(compose_path, project_name, debug_info)
                return [TextContent(type="text", text=result)]
            finally:
                PodmanHandlers._cleanup_files(compose_path)

        except Exception as e:
            debug_output = "\n".join(debug_info)
            return [TextContent(type="text", text=f"Error deploying compose stack: {str(e)}\n\nDebug Information:\n{debug_output}")]

    @staticmethod
    def _process_yaml(compose_yaml: str, debug_info: List[str]) -> dict:
        debug_info.append("=== Original YAML ===")
        debug_info.append(compose_yaml)

        try:
            yaml_content = yaml.safe_load(compose_yaml)
            debug_info.append("\n=== Loaded YAML Structure ===")
            debug_info.append(str(yaml_content))
            return yaml_content
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

    @staticmethod
    def _save_compose_file(yaml_content: dict, project_name: str) -> str:
        compose_dir = os.path.join(os.getcwd(), "podman_compose_files")
        os.makedirs(compose_dir, exist_ok=True)

        compose_yaml = yaml.safe_dump(
            yaml_content, default_flow_style=False, sort_keys=False)
        compose_path = os.path.join(
            compose_dir, f"{project_name}-podman-compose.yml")

        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(compose_yaml)
            f.flush()
            if platform.system() != 'Windows':
                os.fsync(f.fileno())

        return compose_path

    @staticmethod
    async def _deploy_stack(compose_path: str, project_name: str, debug_info: List[str]) -> str:
        compose = PodmanComposeExecutor(compose_path, project_name)

        for command in [compose.down, compose.up]:
            try:
                code, out, err = await command()
                debug_info.extend([
                    f"\n=== {command.__name__.capitalize()} Command ===",
                    f"Return Code: {code}",
                    f"Stdout: {out}",
                    f"Stderr: {err}"
                ])

                if code != 0 and command == compose.up:
                    raise Exception(f"Deploy failed with code {code}: {err}")
            except Exception as e:
                if command != compose.down:
                    raise e
                debug_info.append(f"Warning during {
                                  command.__name__}: {str(e)}")

        code, out, err = await compose.ps()
        service_info = out if code == 0 else "Unable to list services"

        return (f"Successfully deployed compose stack '{project_name}'\n"
                f"Running services:\n{service_info}\n\n"
                f"Debug Info:\n{chr(10).join(debug_info)}")

    @staticmethod
    def _cleanup_files(compose_path: str) -> None:
        try:
            if os.path.exists(compose_path):
                os.remove(compose_path)
            compose_dir = os.path.dirname(compose_path)
            if os.path.exists(compose_dir) and not os.listdir(compose_dir):
                os.rmdir(compose_dir)
        except Exception as e:
            print(f"Warning during cleanup: {str(e)}")

    @staticmethod
    async def handle_get_logs(arguments: Dict[str, Any]) -> List[TextContent]:
        debug_info = []
        try:
            container_name = arguments.get("container_name")
            if not container_name:
                raise ValueError("Missing required container_name")

            debug_info.append(f"Fetching logs for container '{container_name}'")
            executor = PodmanContainerExecutor()
            code, out, err = await executor.logs(container_name)

            if code != 0:
                raise Exception(f"Failed to get logs: {err}")

            return [TextContent(type="text", text=f"Logs for container '{container_name}':\n{out}\n\nDebug Info:\n{chr(10).join(debug_info)}")]
        except Exception as e:
            debug_output = "\n".join(debug_info)
            return [TextContent(type="text", text=f"Error retrieving logs: {str(e)}\n\nDebug Information:\n{debug_output}")]

    @staticmethod
    async def handle_list_containers(arguments: Dict[str, Any]) -> List[TextContent]:
        debug_info = []
        try:
            debug_info.append("Listing all Podman containers")
            executor = PodmanContainerExecutor()
            code, out, err = await executor.ps()

            if code != 0:
                raise Exception(f"Failed to list containers: {err}")

            return [TextContent(type="text", text=f"All Podman Containers:\n{out}\n\nDebug Info:\n{chr(10).join(debug_info)}")]
        except Exception as e:
            debug_output = "\n".join(debug_info)
            return [TextContent(type="text", text=f"Error listing containers: {str(e)}\n\nDebug Information:\n{debug_output}")]
