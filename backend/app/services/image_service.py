"""Docker 镜像业务服务模块。"""

import json
import logging
from typing import Optional
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import docker
from docker.errors import DockerException, ImageNotFound

from app.core.exceptions import (
    ImageDeleteError,
    ImageNotFoundError,
    ImagePullError,
    ImageServiceError,
)

logger = logging.getLogger(__name__)

DOCKER_HUB_SEARCH_URL = "https://hub.docker.com/v2/search/repositories/"
DOCKER_HUB_TAGS_URL_TEMPLATE = (
    "https://hub.docker.com/v2/repositories/{repository}/tags"
)
DEFAULT_PAGE_SIZE = 20


class ImageService:
    """镜像管理服务。"""

    def __init__(self) -> None:
        """初始化镜像服务。"""
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        """获取 Docker 客户端。

        Returns:
            docker.DockerClient: Docker 客户端

        Raises:
            ImageServiceError: Docker 不可用时抛出
        """
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as exc:
                logger.error("连接 Docker 失败", exc_info=True)
                raise ImageServiceError("无法连接 Docker 守护进程") from exc
        return self._client

    @staticmethod
    def build_image_ref(
        repository: str, tag: str, registry: Optional[str] = None
    ) -> str:
        """构建镜像引用。

        Args:
            repository: 镜像仓库
            tag: 镜像版本
            registry: 自定义仓库地址

        Returns:
            str: 镜像引用
        """
        if registry:
            clean_registry = registry.rstrip("/")
            return f"{clean_registry}/{repository}:{tag}"
        return f"{repository}:{tag}"

    async def list_local_images(self) -> list[dict[str, object]]:
        """获取本地镜像列表。

        Returns:
            list[dict[str, object]]: 本地镜像信息列表

        Raises:
            ImageServiceError: 查询失败时抛出
        """
        try:
            images = self.client.images.list()
            payload: list[dict[str, object]] = []
            for image in images:
                tags = image.tags or []
                repo_digests = image.attrs.get("RepoDigests", [])
                payload.append(
                    {
                        "id": image.short_id,
                        "tags": tags,
                        "digests": repo_digests,
                        "size": image.attrs.get("Size", 0),
                        "created": image.attrs.get("Created", ""),
                    }
                )
            return payload
        except DockerException as exc:
            logger.error("读取本地镜像失败", exc_info=True)
            raise ImageServiceError("读取本地镜像失败") from exc

    async def image_exists_locally(self, image_ref: str) -> bool:
        """检查镜像是否存在于本地。

        Args:
            image_ref: 镜像引用

        Returns:
            bool: 是否存在
        """
        try:
            self.client.images.get(image_ref)
            return True
        except ImageNotFound:
            return False
        except DockerException:
            return False

    async def pull_image(self, image_ref: str) -> dict[str, object]:
        """拉取镜像。

        Args:
            image_ref: 镜像引用

        Returns:
            dict[str, object]: 拉取结果

        Raises:
            ImagePullError: 拉取失败时抛出
        """
        try:
            image = self.client.images.pull(image_ref)
            repo_digests = image.attrs.get("RepoDigests", [])
            return {
                "image_ref": image_ref,
                "id": image.short_id,
                "digest": repo_digests[0] if repo_digests else None,
            }
        except DockerException as exc:
            logger.error("拉取镜像失败: image=%s", image_ref, exc_info=True)
            raise ImagePullError(image_ref, str(exc)) from exc

    async def search_repositories(
        self,
        query: str,
        registry: Optional[str] = None,
    ) -> list[dict[str, object]]:
        """搜索镜像仓库。

        Args:
            query: 搜索关键字
            registry: 自定义仓库地址（可选）

        Returns:
            list[dict[str, object]]: 搜索结果

        Raises:
            ImageServiceError: 搜索失败时抛出
        """
        if registry:
            return [
                {
                    "name": query,
                    "description": "自定义仓库不支持在线搜索，请手动输入完整仓库名",
                    "registry": registry,
                    "is_official": False,
                    "star_count": 0,
                }
            ]

        params = urlencode({"query": query, "page_size": DEFAULT_PAGE_SIZE})
        request = Request(f"{DOCKER_HUB_SEARCH_URL}?{params}", method="GET")

        try:
            with urlopen(request, timeout=15) as response:
                raw_data = response.read().decode("utf-8")
                payload = json.loads(raw_data)
                result_items = payload.get("results", [])
                return [
                    {
                        "name": item.get("repo_name", ""),
                        "description": item.get("short_description", ""),
                        "registry": "docker.io",
                        "is_official": bool(item.get("is_official", False)),
                        "star_count": int(item.get("star_count", 0)),
                    }
                    for item in result_items
                ]
        except Exception as exc:
            logger.error("搜索镜像仓库失败", exc_info=True)
            raise ImageServiceError("搜索镜像仓库失败，请稍后重试") from exc

    async def list_tags(
        self, repository: str, registry: Optional[str] = None
    ) -> list[str]:
        """获取镜像版本列表。

        Args:
            repository: 镜像仓库
            registry: 自定义仓库地址（可选）

        Returns:
            list[str]: 版本标签列表

        Raises:
            ImageServiceError: 查询失败时抛出
        """
        if registry:
            tags_url = f"https://{registry.rstrip('/')}/v2/{repository}/tags/list"
            request = Request(tags_url, method="GET")
            try:
                with urlopen(request, timeout=15) as response:
                    raw_data = response.read().decode("utf-8")
                    payload = json.loads(raw_data)
                    registry_tags = payload.get("tags", [])
                    return sorted([str(tag) for tag in registry_tags], reverse=True)
            except Exception as exc:
                logger.error("读取自定义仓库 tags 失败", exc_info=True)
                raise ImageServiceError(
                    "读取自定义仓库 tags 失败，请检查仓库地址与权限"
                ) from exc

        encoded_repository = quote(repository, safe="/")
        request = Request(
            f"{DOCKER_HUB_TAGS_URL_TEMPLATE.format(repository=encoded_repository)}?page_size=100",
            method="GET",
        )
        try:
            with urlopen(request, timeout=15) as response:
                raw_data = response.read().decode("utf-8")
                payload = json.loads(raw_data)
                result_items = payload.get("results", [])
                hub_tags: list[str] = [
                    str(item.get("name", ""))
                    for item in result_items
                    if item.get("name")
                ]
                return hub_tags
        except Exception as exc:
            logger.error("读取镜像 tags 失败", exc_info=True)
            raise ImageServiceError("读取镜像版本失败，请稍后重试") from exc

    async def ensure_image_available(
        self, image_ref: str, allow_pull: bool
    ) -> dict[str, object]:
        """确保镜像可用。

        Args:
            image_ref: 镜像引用
            allow_pull: 是否允许自动拉取

        Returns:
            dict[str, object]: 可用性信息

        Raises:
            ImageNotFoundError: 镜像不存在且不允许拉取时抛出
            ImagePullError: 拉取失败时抛出
        """
        if await self.image_exists_locally(image_ref):
            image = self.client.images.get(image_ref)
            repo_digests = image.attrs.get("RepoDigests", [])
            return {
                "image_ref": image_ref,
                "available": True,
                "pulled": False,
                "digest": repo_digests[0] if repo_digests else None,
            }

        if not allow_pull:
            raise ImageNotFoundError(image_ref)

        pull_result = await self.pull_image(image_ref)
        return {
            "image_ref": image_ref,
            "available": True,
            "pulled": True,
            "digest": pull_result.get("digest"),
        }

    async def remove_local_image(
        self, image_ref: str, force: bool = False
    ) -> dict[str, object]:
        """删除本地镜像。

        Args:
            image_ref: 镜像引用（repository:tag 或 image id）
            force: 是否强制删除

        Returns:
            dict[str, object]: 删除结果

        Raises:
            ImageNotFoundError: 镜像不存在时抛出
            ImageDeleteError: 删除失败时抛出
        """
        try:
            self.client.images.remove(image=image_ref, force=force, noprune=False)
            return {"image_ref": image_ref, "removed": True, "force": force}
        except ImageNotFound as exc:
            logger.error("删除镜像失败，镜像不存在: image=%s", image_ref, exc_info=True)
            raise ImageNotFoundError(image_ref) from exc
        except DockerException as exc:
            logger.error(
                "删除镜像失败: image=%s, force=%s", image_ref, force, exc_info=True
            )
            raise ImageDeleteError(image_ref, str(exc)) from exc
