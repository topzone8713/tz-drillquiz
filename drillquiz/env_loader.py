"""
Custom environment variable loader for DrillQuiz
Priority: Secret > ConfigMap > System Environment > .env file
"""

import os
from decouple import Config, RepositoryEnv
from pathlib import Path


class KubernetesAwareConfig:
    """
    Custom configuration loader that respects Kubernetes Secret/ConfigMap precedence
    Priority order:
    1. Kubernetes Secret (highest)
    2. Kubernetes ConfigMap
    3. System Environment Variables
    4. .env file (lowest)
    """
    
    def __init__(self, env_file_path=None):
        self.env_file_path = env_file_path or Path('.env')
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration with proper precedence"""
        # Start with .env file as base
        if self.env_file_path.exists():
            self._config = Config(RepositoryEnv(self.env_file_path))
        else:
            # Create an empty repository for Config
            from decouple import RepositoryEmpty
            self._config = Config(RepositoryEmpty())
    
    def get(self, key, default=None, cast=None):
        """
        Get configuration value with proper precedence
        
        Args:
            key: Configuration key
            default: Default value if not found
            cast: Type casting function (e.g., bool, int)
        
        Returns:
            Configuration value with proper type casting
        """
        # Debug: Print the source of each value
        debug_enabled = os.environ.get('DEBUG_ENV_LOADER', 'False').lower() == 'true'
        
        # Priority 1: Kubernetes Secret (check if running in K8s)
        if self._is_kubernetes_environment():
            secret_value = self._get_kubernetes_secret(key)
            if secret_value is not None:
                if debug_enabled:
                    print(f"[ENV_LOADER] {key}: Secret -> {secret_value}")
                return self._cast_value(secret_value, cast)
        
        # Priority 2: Kubernetes ConfigMap (check if running in K8s)
        if self._is_kubernetes_environment():
            configmap_value = self._get_kubernetes_configmap(key)
            if configmap_value is not None:
                if debug_enabled:
                    print(f"[ENV_LOADER] {key}: ConfigMap -> {configmap_value}")
                return self._cast_value(configmap_value, cast)
        
        # Priority 3: System Environment Variable
        env_value = os.environ.get(key)
        if env_value is not None:
            if debug_enabled:
                print(f"[ENV_LOADER] {key}: System ENV -> {env_value}")
            return self._cast_value(env_value, cast)
        
        # Priority 4: .env file
        try:
            env_file_value = self._config.get(key, default=None)
            if env_file_value is not None:
                if debug_enabled:
                    print(f"[ENV_LOADER] {key}: .env file -> {env_file_value}")
                return self._cast_value(env_file_value, cast)
        except Exception:
            pass
        
        # Return default value
        if debug_enabled:
            print(f"[ENV_LOADER] {key}: Default -> {default}")
        return self._cast_value(default, cast)
    
    def _is_kubernetes_environment(self):
        """Check if running in Kubernetes environment"""
        # Check for Kubernetes-specific environment variables
        k8s_indicators = [
            'KUBERNETES_SERVICE_HOST',
            'KUBERNETES_SERVICE_PORT',
            'KUBERNETES_PORT',
            'HOSTNAME',  # Pod hostname
        ]
        
        # Check if any Kubernetes indicator exists
        for indicator in k8s_indicators:
            if os.environ.get(indicator):
                return True
        
        # Check if running in a container with typical K8s patterns
        hostname = os.environ.get('HOSTNAME', '')
        if hostname and ('-' in hostname and len(hostname.split('-')) >= 3):
            # Typical K8s pod naming pattern: app-name-randomstring
            return True
        
        return False
    
    def _get_kubernetes_secret(self, key):
        """
        Get value from Kubernetes Secret
        In Kubernetes, secrets are mounted as environment variables
        """
        # Kubernetes secrets are typically mounted as environment variables
        # with the same name as the secret key
        return os.environ.get(key)
    
    def _get_kubernetes_configmap(self, key):
        """
        Get value from Kubernetes ConfigMap
        In Kubernetes, configmaps are mounted as environment variables
        """
        # Kubernetes configmaps are typically mounted as environment variables
        # with the same name as the configmap key
        return os.environ.get(key)
    
    def _cast_value(self, value, cast):
        """Cast value to specified type"""
        if value is None:
            return None
        
        if cast is None:
            return value
        
        try:
            if cast == bool:
                # Handle boolean casting for string values
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            return cast(value)
        except (ValueError, TypeError):
            return value


# Global config instance
config = KubernetesAwareConfig()


def get_config(key, default=None, cast=None):
    """
    Convenience function to get configuration value
    
    Args:
        key: Configuration key
        default: Default value if not found
        cast: Type casting function
    
    Returns:
        Configuration value
    """
    return config.get(key, default, cast) 