from pathlib import Path
from typing import Tuple, List

from etcd_setup.core import BaseBuilder, BuildSpec, prune_cache_images, BuildahContainer, init_base_distro


class RuntimeBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = "", image_name: str = "", image_tag: str = "",
                 remove_package_manager: bool = True,
                 squash: bool = True):
        super().__init__(config, cache_prefix)

        if len(image_name) > 0:
            self.image_name = image_name
        else:
            self.image_name = f"{self.config.ProjectName}-runtime"

        if len(image_tag) > 0:
            self.image_tag = image_tag
        else:
            self.image_tag = self.config.Etcd.Version
        self.remove_package_manager = remove_package_manager
        self.squash = squash

    def _init_cache_prefix(self, cache_prefix: str):
        if len(cache_prefix) > 0:
            self.cache_prefix = cache_prefix
        else:
            self.cache_prefix = f"{self.config.ProjectName}/cache/runtime/{self.config.Etcd.Version}"

    def build(self):
        self.log(f"Starting build for Etcd {self.config.Etcd.Version} runtime",
                 style="bold blue")

        current_step = 1

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            base_distro = init_base_distro(self.config.Distro, container)

            self.log(f"[bold blue]Step {current_step}[/bold blue]: Retrieving etcd artifacts")

            self.image_tag = self.config.Etcd.Version

            container.copy_container_current(
                f"{self.config.ProjectName}-core:{self.config.Etcd.Version}",
                self.config.Etcd.Prefix,
                self.config.Etcd.Prefix
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Installing etcd runtime dependencies")

            base_distro.refresh_package_repository()

            base_distro.install_packages(
                packages=self.config.Etcd.Runtime.Dependencies,
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.Etcd.Runtime.Dependencies)}
            )

            container.run(command=["zypper", "clean", "--all"])

            if self.config.Etcd.Runtime.RemoveDependencies:
                base_distro.remove_packages(
                    packages=self.config.Etcd.Runtime.RemoveDependencies
                )

            container.run(
                command=["update-ca-certificates"]
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Setting up system user")

            container.run(
                command=["groupadd", "-r", "-g", str(self.config.Etcd.Runtime.Gid), "etcd"]
            )

            container.run(
                command=["useradd", "-r", "-u", str(self.config.Etcd.Runtime.Uid), "-g",
                         str(self.config.Etcd.Runtime.Gid), "-d", self.config.Etcd.Prefix, "-s",
                         "/sbin/nologin", "-c",
                         '"Etcd Server"', "etcd"]
            )

            container.configure(
                [
                    ("--label", f"io.etcd.user.uid={self.config.Etcd.Runtime.Uid}"),
                    ("--label", f"io.etcd.user.gid={self.config.Etcd.Runtime.Gid}"),
                    ("--label", f"io.etcd.user.name=etcd"),
                ]
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Setting up directories & permissions")

            env_configuration: List[Tuple[str, str]] = []
            if self.config.Etcd.Runtime.Environment:
                for env in self.config.Etcd.Runtime.Environment:
                    env_configuration.append(("--env", env))

            container.configure([
                                    ("--env",
                                     f"PATH={self.config.Etcd.Prefix}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
                                ] + env_configuration)

            container.run(["mkdir","-p", self.config.Etcd.Runtime.DataDir])
            container.configure([
                ("--volume", self.config.Etcd.Runtime.DataDir),
                ("--env",f"ETCD_DATA_DIR={self.config.Etcd.Runtime.DataDir}")
            ])

            container.run(
                command=["chown", "-R",
                         f"{self.config.Etcd.Runtime.Uid}:{self.config.Etcd.Runtime.Gid}",
                         self.config.Etcd.Prefix]
            )

            container.copy_host_container(Path(f"{self.config.Etcd.Runtime.Resources}/entrypoint.sh"),
                                          "/usr/local/bin/entrypoint.sh")
            container.run(command=["chmod", "+x", "/usr/local/bin/entrypoint.sh"])

            if self.remove_package_manager:
                if not self.squash:
                    self.log("[bold yellow]Warning[/bold yellow]: Please enable squashing to reduce image size.")
                self.log("[blue dim]Removing package manager[/blue dim]")
                base_distro.remove_package_manager()

            container.configure([
                ("--entrypoint", '["/usr/local/bin/entrypoint.sh"]'),
                ("--cmd", '[]'),
                ("--user", str(self.config.Etcd.Runtime.Uid)),
            ])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Tagging image and adding metadata.")

            container.configure([
                ("--label", f"org.etcd.version={self.config.Etcd.Version}"),
                ("--label", f"org.etcd.prefix={self.config.Etcd.Prefix}"),
            ])
            if self.config.Etcd.Runtime.Ports:
                for port in self.config.Etcd.Runtime.Ports:
                    container.configure([
                        ("--port", f"{port}")
                    ])
            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")

    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)
