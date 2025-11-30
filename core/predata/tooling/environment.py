"""Environment profiling."""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import platform
import os


@dataclass
class EnvironmentProfile:
    """System environment profile."""
    platform: str
    python_version: str
    hostname: str
    cpu_count: int
    memory_gb: Optional[float]
    gpu_available: bool
    container: bool
    cloud_provider: Optional[str]
    custom_tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "python_version": self.python_version,
            "hostname": self.hostname,
            "cpu_count": self.cpu_count,
            "memory_gb": self.memory_gb,
            "gpu_available": self.gpu_available,
            "container": self.container,
            "cloud_provider": self.cloud_provider,
            "custom_tags": self.custom_tags,
        }


class EnvironmentProfiler:
    """
    Profiles the execution environment.
    
    Usage:
        profiler = EnvironmentProfiler()
        profile = profiler.get_profile()
    """
    
    def __init__(self):
        self._cached_profile: Optional[EnvironmentProfile] = None
        self._custom_tags: Dict[str, str] = {}
    
    def add_tag(self, key: str, value: str) -> None:
        """Add custom environment tag."""
        self._custom_tags[key] = value
        self._cached_profile = None  # Invalidate cache
    
    def get_profile(self, refresh: bool = False) -> EnvironmentProfile:
        """Get environment profile."""
        if self._cached_profile and not refresh:
            return self._cached_profile
        
        profile = EnvironmentProfile(
            platform=platform.system(),
            python_version=platform.python_version(),
            hostname=platform.node(),
            cpu_count=os.cpu_count() or 1,
            memory_gb=self._get_memory(),
            gpu_available=self._check_gpu(),
            container=self._is_container(),
            cloud_provider=self._detect_cloud(),
            custom_tags=self._custom_tags.copy(),
        )
        
        self._cached_profile = profile
        return profile
    
    def _get_memory(self) -> Optional[float]:
        """Get system memory in GB."""
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        return round(kb / 1024 / 1024, 2)
        except:
            pass
        return None
    
    def _check_gpu(self) -> bool:
        """Check if GPU is available."""
        # Check for NVIDIA GPU
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi'], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            pass
        
        # Check for CUDA env vars
        if os.environ.get('CUDA_VISIBLE_DEVICES'):
            return True
        
        return False
    
    def _is_container(self) -> bool:
        """Check if running in container."""
        # Docker
        if os.path.exists('/.dockerenv'):
            return True
        
        # Kubernetes
        if os.environ.get('KUBERNETES_SERVICE_HOST'):
            return True
        
        # Check cgroup
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'kubepods' in content:
                    return True
        except:
            pass
        
        return False
    
    def _detect_cloud(self) -> Optional[str]:
        """Detect cloud provider."""
        # AWS
        if os.environ.get('AWS_REGION') or os.environ.get('AWS_EXECUTION_ENV'):
            return "aws"
        
        # GCP
        if os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT'):
            return "gcp"
        
        # Azure
        if os.environ.get('AZURE_SUBSCRIPTION_ID') or os.environ.get('WEBSITE_SITE_NAME'):
            return "azure"
        
        return None
