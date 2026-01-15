from etcd_setup.core import BaseBuilder, BuildahContainer, prune_cache_images, BuildSpec, init_base_distro


class CoreBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = ""):
        super().__init__(config, cache_prefix)
        self.image_name = f"{self.config.ProjectName}-core"
        self.image_tag = self.config.Etcd.Version

    def _init_cache_prefix(self, cache_prefix: str):
        if len(cache_prefix) > 0:
            self.cache_prefix = cache_prefix
        else:
            self.cache_prefix = f"{self.config.ProjectName}/cache/core/{self.config.Etcd.Version}"

    def build(self):
        self.log(f"Starting build for Etcd {self.config.Etcd.Version} core", style="bold blue")

        current_step = 1
        total_no_of_steps = 4

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            base_distro = init_base_distro(self.config.Distro, container)

            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Installing build dependencies")

            base_distro.refresh_package_repository()

            base_distro.install_packages(
                packages=self.config.Etcd.Build.Dependencies,
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.Etcd.Build.Dependencies)}
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Preparing directory {self.config.Etcd.Prefix}")

            container.run(["mkdir", "-p", f"{self.config.Etcd.Prefix}/bin"])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Downloading and Extracting from {self.config.Etcd.SourceUrl}")

            tar_path = f"/tmp/etcd-{self.config.Etcd.Version}.tar.gz"

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                            curl -L '{self.config.Etcd.SourceUrl}' -o {tar_path} && 
                            tar -xzf {tar_path} -C {self.config.Etcd.Prefix}/bin --strip-components=1 --no-same-owner &&
                            rm {tar_path}
                            """
                ],
                extra_cache_keys={
                    "step": "download_extract",
                    "url": self.config.Etcd.SourceUrl,
                    "prefix": self.config.Etcd.Prefix
                }
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Verifying installation and committing.")

            try:
                etcd_bin = f"{self.config.Etcd.Prefix}/bin/etcd"
                container.run(["test", "-x", etcd_bin])

                self.log(f"Verification successful: Found {etcd_bin}", style="bold green")
            except Exception:
                self.log("[bold red]Verification Failed[/bold red]: Etcd binary missing in extraction path.")
                raise

            container.configure([
                ("--label", f"org.etcd.version={self.config.Etcd.Version}"),
                ("--label", f"org.etcd.prefix={self.config.Etcd.Prefix}"),
            ])

            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")

    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)
