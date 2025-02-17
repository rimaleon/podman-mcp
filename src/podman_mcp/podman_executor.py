from typing import Tuple, Protocol, List
import asyncio
import os
import platform
import shutil
from abc import ABC, abstractmethod


class CommandExecutor(Protocol):
    async def execute(self, cmd: str | List[str]) -> Tuple[int, str, str]:
        pass


class WindowsExecutor:
    async def execute(self, cmd: str) -> Tuple[int, str, str]:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()


class UnixExecutor:
    async def execute(self, cmd: List[str]) -> Tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()


class PodmanExecutorBase(ABC):
    def __init__(self):
        self.podman_cmd = self._initialize_podman_cmd()
        self.executor = WindowsExecutor() if platform.system() == 'Windows' else UnixExecutor()

    @abstractmethod
    async def run_command(self, command: str, *args) -> Tuple[int, str, str]:
        pass

    def _initialize_podman_cmd(self) -> str:
        if platform.system() == 'Windows':
            podman_paths = [
                r"C:\Program Files\RedHat\Podman\podman.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\podman\podman.exe")
            ]
            for path in podman_paths:
                if os.path.exists(path):
                    return path

        podman_cmd = shutil.which('podman')
        if not podman_cmd:
            raise RuntimeError("Podman executable not found")
        return podman_cmd


class PodmanComposeExecutor(PodmanExecutorBase):
    def __init__(self, compose_file: str, project_name: str):
        super().__init__()
        self.compose_file = os.path.abspath(compose_file)
        self.project_name = project_name

    async def run_command(self, command: str, *args) -> Tuple[int, str, str]:
        if platform.system() == 'Windows':
            cmd = self._build_windows_command(command, *args)
        else:
            cmd = self._build_unix_command(command, *args)
        return await self.executor.execute(cmd)

    def _build_windows_command(self, command: str, *args) -> str:
        compose_file = self.compose_file.replace('\\', '/')
        return (f'cd "{os.path.dirname(compose_file)}" && podman-compose '
                f'-f "{os.path.basename(compose_file)}" '
                f'-p {self.project_name} {command} {" ".join(args)}')

    def _build_unix_command(self, command: str, *args) -> list[str]:
        return [
            "podman-compose",
            "-f", self.compose_file,
            "-p", self.project_name,
            command,
            *args
        ]

    async def down(self) -> Tuple[int, str, str]:
        return await self.run_command("down", "--volumes")

    async def pull(self) -> Tuple[int, str, str]:
        return await self.run_command("pull")

    async def up(self) -> Tuple[int, str, str]:
        return await self.run_command("up", "-d")

    async def ps(self) -> Tuple[int, str, str]:
        return await self.run_command("ps")


class PodmanContainerExecutor(PodmanExecutorBase):
    async def run_command(self, command: str, *args) -> Tuple[int, str, str]:
        if platform.system() == 'Windows':
            cmd = f'"{self.podman_cmd}" {command} {" ".join(args)}'
        else:
            cmd = [self.podman_cmd, command, *args]
        return await self.executor.execute(cmd)

    async def run(self, image: str, name: str, ports: dict, environment: dict) -> Tuple[int, str, str]:
        args = ["--name", name]
        
        for container_port, host_port in ports.items():
            args.extend(["-p", f"{host_port}:{container_port}"])
        
        for key, value in environment.items():
            args.extend(["-e", f"{key}={value}"])
        
        args.append(image)
        return await self.run_command("run", "-d", *args)

    async def logs(self, container_name: str) -> Tuple[int, str, str]:
        return await self.run_command("logs", container_name)

    async def ps(self) -> Tuple[int, str, str]:
        return await self.run_command("ps") 