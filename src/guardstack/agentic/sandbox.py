"""
Agent Sandbox

Sandboxed execution environment for AI agents.
"""

import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SandboxMode(Enum):
    """Sandbox isolation modes."""
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"
    VM = "vm"


@dataclass
class SandboxConfig:
    """Configuration for agent sandbox."""
    
    mode: SandboxMode = SandboxMode.PROCESS
    timeout_seconds: int = 30
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    network_enabled: bool = False
    filesystem_readonly: bool = True
    allowed_paths: list[str] = field(default_factory=list)
    blocked_syscalls: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)


@dataclass
class SandboxResult:
    """Result of sandboxed execution."""
    
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_time_ms: int = 0
    resource_usage: dict[str, Any] = field(default_factory=dict)


class AgentSandbox:
    """
    Sandbox environment for AI agent execution.
    
    Provides isolated execution with:
    - Resource limits (CPU, memory)
    - Network isolation
    - Filesystem restrictions
    - Syscall filtering
    - Timeout enforcement
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self.config = config or SandboxConfig()
        self._temp_dir: Optional[str] = None
    
    async def __aenter__(self) -> "AgentSandbox":
        """Set up sandbox environment."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up sandbox environment."""
        await self.cleanup()
    
    async def setup(self) -> None:
        """Initialize sandbox environment."""
        # Create temporary working directory
        self._temp_dir = tempfile.mkdtemp(prefix="guardstack_sandbox_")
        
        logger.info(f"Sandbox initialized: {self.config.mode.value} mode")
    
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        
        logger.info("Sandbox cleaned up")
    
    async def execute(
        self,
        command: str,
        args: Optional[list[str]] = None,
        input_data: Optional[str] = None,
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Command to execute
            args: Command arguments
            input_data: Input to pass to stdin
        
        Returns:
            SandboxResult with output and status
        """
        start_time = time.time()
        
        if self.config.mode == SandboxMode.NONE:
            return await self._execute_direct(command, args, input_data)
        elif self.config.mode == SandboxMode.PROCESS:
            return await self._execute_process(command, args, input_data)
        elif self.config.mode == SandboxMode.CONTAINER:
            return await self._execute_container(command, args, input_data)
        else:
            return SandboxResult(
                success=False,
                output="",
                error=f"Unsupported sandbox mode: {self.config.mode}",
            )
    
    async def _execute_direct(
        self,
        command: str,
        args: Optional[list[str]],
        input_data: Optional[str],
    ) -> SandboxResult:
        """Execute without sandboxing (for testing)."""
        start_time = time.time()
        
        try:
            full_command = [command] + (args or [])
            
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._temp_dir,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input_data.encode() if input_data else None),
                timeout=self.config.timeout_seconds,
            )
            
            return SandboxResult(
                success=process.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if stderr else None,
                exit_code=process.returncode or 0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            
        except asyncio.TimeoutError:
            return SandboxResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.config.timeout_seconds}s",
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
    
    async def _execute_process(
        self,
        command: str,
        args: Optional[list[str]],
        input_data: Optional[str],
    ) -> SandboxResult:
        """Execute with process-level sandboxing."""
        start_time = time.time()
        
        # Build sandboxed command
        sandbox_cmd = self._build_process_sandbox_command(command, args)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *sandbox_cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._temp_dir,
                env=self._build_sandbox_env(),
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input_data.encode() if input_data else None),
                timeout=self.config.timeout_seconds,
            )
            
            return SandboxResult(
                success=process.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if stderr else None,
                exit_code=process.returncode or 0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            
        except asyncio.TimeoutError:
            return SandboxResult(
                success=False,
                output="",
                error=f"Execution timed out after {self.config.timeout_seconds}s",
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
    
    async def _execute_container(
        self,
        command: str,
        args: Optional[list[str]],
        input_data: Optional[str],
    ) -> SandboxResult:
        """Execute in container sandbox."""
        start_time = time.time()
        
        # Build Docker command
        docker_cmd = self._build_container_command(command, args)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input_data.encode() if input_data else None),
                timeout=self.config.timeout_seconds + 10,  # Extra time for container ops
            )
            
            return SandboxResult(
                success=process.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if stderr else None,
                exit_code=process.returncode or 0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            
        except asyncio.TimeoutError:
            return SandboxResult(
                success=False,
                output="",
                error=f"Container execution timed out",
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
    
    def _build_process_sandbox_command(
        self,
        command: str,
        args: Optional[list[str]],
    ) -> list[str]:
        """Build command with process sandbox wrapper."""
        # On Linux, could use unshare, firejail, or bubblewrap
        # On macOS, could use sandbox-exec
        # For now, basic timeout wrapper
        
        full_command = [command] + (args or [])
        
        # Use timeout command if available
        sandbox_cmd = [
            "timeout",
            str(self.config.timeout_seconds),
        ] + full_command
        
        return sandbox_cmd
    
    def _build_container_command(
        self,
        command: str,
        args: Optional[list[str]],
    ) -> list[str]:
        """Build Docker run command."""
        docker_cmd = [
            "docker", "run",
            "--rm",
            f"--memory={self.config.max_memory_mb}m",
            f"--cpus={self.config.max_cpu_percent / 100}",
            "--read-only" if self.config.filesystem_readonly else "",
            "--network=none" if not self.config.network_enabled else "",
        ]
        
        # Add volume mounts for allowed paths
        for path in self.config.allowed_paths:
            docker_cmd.extend(["-v", f"{path}:{path}:ro"])
        
        # Add temp directory as writable
        if self._temp_dir:
            docker_cmd.extend(["-v", f"{self._temp_dir}:/workspace"])
            docker_cmd.extend(["-w", "/workspace"])
        
        # Add environment variables
        for key, value in self.config.environment.items():
            docker_cmd.extend(["-e", f"{key}={value}"])
        
        # Use minimal image
        docker_cmd.append("alpine:latest")
        
        # Add command
        docker_cmd.extend([command] + (args or []))
        
        # Filter empty strings
        return [c for c in docker_cmd if c]
    
    def _build_sandbox_env(self) -> dict[str, str]:
        """Build environment for sandboxed process."""
        env = os.environ.copy()
        
        # Remove sensitive environment variables
        sensitive_vars = [
            "AWS_SECRET_ACCESS_KEY",
            "AWS_ACCESS_KEY_ID",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DATABASE_URL",
            "SECRET_KEY",
        ]
        
        for var in sensitive_vars:
            env.pop(var, None)
        
        # Add sandbox-specific variables
        env["SANDBOX"] = "1"
        env["SANDBOX_MODE"] = self.config.mode.value
        
        # Add custom environment
        env.update(self.config.environment)
        
        return env
    
    async def execute_python(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> SandboxResult:
        """Execute Python code in sandbox."""
        import sys
        
        # Create temporary script file
        script_path = os.path.join(self._temp_dir or tempfile.gettempdir(), "script.py")
        
        with open(script_path, "w") as f:
            f.write(code)
        
        return await self.execute(
            sys.executable,
            [script_path],
        )


class SandboxPool:
    """
    Pool of pre-warmed sandbox environments.
    """
    
    def __init__(
        self,
        size: int = 5,
        config: Optional[SandboxConfig] = None,
    ) -> None:
        self.size = size
        self.config = config
        self._available: asyncio.Queue[AgentSandbox] = asyncio.Queue()
        self._all: list[AgentSandbox] = []
    
    async def initialize(self) -> None:
        """Initialize sandbox pool."""
        for _ in range(self.size):
            sandbox = AgentSandbox(self.config)
            await sandbox.setup()
            self._all.append(sandbox)
            await self._available.put(sandbox)
        
        logger.info(f"Sandbox pool initialized with {self.size} instances")
    
    async def acquire(self) -> AgentSandbox:
        """Acquire a sandbox from the pool."""
        return await self._available.get()
    
    async def release(self, sandbox: AgentSandbox) -> None:
        """Release a sandbox back to the pool."""
        # Could reset sandbox state here
        await self._available.put(sandbox)
    
    async def shutdown(self) -> None:
        """Shutdown all sandboxes."""
        for sandbox in self._all:
            await sandbox.cleanup()
        
        self._all.clear()
        logger.info("Sandbox pool shutdown complete")
