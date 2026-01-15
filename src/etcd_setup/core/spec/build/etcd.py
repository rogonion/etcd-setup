from typing import List

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)
    RemoveDependencies: List[str] = Field(default_factory=list)
    Environment: List[str] = Field(default_factory=list)
    DataDir: str = Field(default_factory=str)
    Resources: str = "resources"
    Uid: int = 1001
    Gid: int = 1001
    Ports: List[int] = Field(default_factory=list)


class BuildConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)


class EtcdConfig(BaseModel):
    Version: str
    SourceUrl: str
    Prefix: str = '/usr/local/etcd'
    Build: BuildConfig = Field(default_factory=BuildConfig)
    Runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
