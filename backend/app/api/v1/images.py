"""Docker 镜像管理 API 路由模块。"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_current_user
from app.core.exceptions import ImageNotFoundError, ImagePullError, ImageServiceError
from app.models.user import User
from app.services.image_service import ImageService

router = APIRouter(prefix="/images", tags=["Images"])


def get_image_service() -> ImageService:
    """获取镜像服务。

    Returns:
        ImageService: 镜像服务实例
    """
    return ImageService()


def success_response(data: object = None, message: str = "操作成功") -> dict[str, object]:
    """生成成功响应。"""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: int = 400) -> dict[str, object]:
    """生成错误响应。"""
    return {"success": False, "message": message, "code": code, "data": None}


class ImagePullRequest(BaseModel):
    """镜像拉取请求。"""

    repository: str = Field(..., min_length=1, max_length=255, description="镜像仓库")
    tag: str = Field(default="latest", min_length=1, max_length=100, description="镜像版本")
    registry: Optional[str] = Field(default=None, description="自定义仓库地址")


@router.get("/search", summary="搜索镜像仓库")
async def search_repositories(
    query: str,
    registry: Optional[str] = None,
    service: ImageService = Depends(get_image_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """搜索镜像仓库。"""
    try:
        repositories = await service.search_repositories(query=query, registry=registry)
        return JSONResponse(content=success_response(data=repositories, message="搜索成功"))
    except ImageServiceError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.get("/tags", summary="获取镜像版本列表")
async def list_tags(
    repository: str,
    registry: Optional[str] = None,
    service: ImageService = Depends(get_image_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """获取镜像版本列表。"""
    try:
        tags = await service.list_tags(repository=repository, registry=registry)
        return JSONResponse(content=success_response(data={"tags": tags}, message="获取版本成功"))
    except ImageServiceError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.get("/local", summary="获取本地镜像列表")
async def list_local_images(
    service: ImageService = Depends(get_image_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """获取本地镜像列表。"""
    try:
        local_images = await service.list_local_images()
        return JSONResponse(content=success_response(data=local_images, message="获取本地镜像成功"))
    except ImageServiceError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


@router.post("/pull", summary="拉取镜像")
async def pull_image(
    request: ImagePullRequest,
    service: ImageService = Depends(get_image_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """拉取镜像。"""
    image_ref = service.build_image_ref(
        repository=request.repository,
        tag=request.tag,
        registry=request.registry,
    )

    try:
        pull_result = await service.pull_image(image_ref)
        return JSONResponse(
            content=success_response(data=pull_result, message="镜像拉取成功"),
        )
    except (ImagePullError, ImageServiceError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )


class ImageAvailabilityRequest(BaseModel):
    """镜像可用性检查请求。"""

    repository: str = Field(..., min_length=1, max_length=255, description="镜像仓库")
    tag: str = Field(default="latest", min_length=1, max_length=100, description="镜像版本")
    registry: Optional[str] = Field(default=None, description="自定义仓库地址")
    allow_pull: bool = Field(default=False, description="是否允许自动拉取")


@router.post("/ensure", summary="确保镜像可用")
async def ensure_image_available(
    request: ImageAvailabilityRequest,
    service: ImageService = Depends(get_image_service),
    _current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """确保镜像可用。"""
    image_ref = service.build_image_ref(
        repository=request.repository,
        tag=request.tag,
        registry=request.registry,
    )

    try:
        availability = await service.ensure_image_available(
            image_ref=image_ref,
            allow_pull=request.allow_pull,
        )
        return JSONResponse(content=success_response(data=availability, message="镜像可用"))
    except ImageNotFoundError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_response(exc.message, status.HTTP_409_CONFLICT),
        )
    except (ImagePullError, ImageServiceError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(exc.message, status.HTTP_400_BAD_REQUEST),
        )
