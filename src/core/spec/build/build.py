from enum import StrEnum

from pydantic import BaseModel, Field

from .etcd import EtcdConfig


class Distro(StrEnum):
    SUSE = "suse"

class BuildahConfig(BaseModel):
    Path: str = 'buildah'


class BuildSpec(BaseModel):
    ProjectName: str
    BaseImage: str
    Distro: Distro
    Buildah: BuildahConfig = Field(default_factory=BuildahConfig)
    Etcd: EtcdConfig = Field(default_factory=EtcdConfig)
