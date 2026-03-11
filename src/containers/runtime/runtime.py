from pathlib import Path
from typing import Optional

import typer

from .builder import RuntimeBuilder
from src.core import BuildSpec, load_spec

app = typer.Typer(help="An etcd runtime.")


@app.command("build", help="Build an etcd runtime.")
def build(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        image_name: Optional[str] = typer.Option("etcd", "--image-name", "--n",
                                                 help="Name of new etcd runtime image."),
        image_tag: Optional[str] = typer.Option("", "--image-tag", "--t",
                                                help="Optional. Tag of new etcd runtime image"),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers."),
        remove_package_manager: Optional[bool] = typer.Option(True, "--remove-package-manager", "--rp",
                                                              help="Optional. Remove dependency manager at the end of image build. Slims the image and improves security."),
        squash: Optional[bool] = typer.Option(True, "--squash", "--sq",
                                              help="Optional. Merge layers into one. Important if remove_package_manager is set to True")
):
    """
    Build Etcd runtime image.

    :param squash:
    :param remove_package_manager:
    :param cache_prefix:
    :param spec_file:
    :param image_name:
    :param image_tag:
    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix, image_name, image_tag, remove_package_manager=remove_package_manager,
                             squash=squash)

    builder.build()


@app.command("delete-cache", help="Delete cache images used to build etcd runtime image.")
def delete_cache(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Delete cache images used to build Etcd runtime.

    :param spec_file: Path to build spec file.
    :param cache_prefix: Custom prefix for cache layers generated.

    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix)

    builder.prune_cache_images()
