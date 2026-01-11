from common.base_router import NO_AUTH, ApiRouter
from common.entity.base_response import BaseResponse
from common.entity.schemas.user import (
    LoginRequest,
    LoginResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
)
from services import UserService

# 默认所有路由需要认证
router = ApiRouter(prefix="/api/v1/user", tags=["user"])


@router.post("/login", response_model=BaseResponse[LoginResponse], dependencies=NO_AUTH)
async def login(request: LoginRequest):
    """
    用户登录

    - 不需要认证
    - 验证用户名和密码
    - 返回 JWT token
    """
    result = await UserService.login(request.username, request.password)
    return BaseResponse(code=0, message="登录成功", data=result)


@router.post("/create", response_model=BaseResponse[UserResponse], dependencies=NO_AUTH)
async def create_user(request: UserCreateRequest):
    """
    创建用户

    - 不需要认证
    - 用户名和邮箱必须唯一
    - 密码会自动哈希
    """
    result = await UserService.create_user(request)
    return BaseResponse(code=0, message="创建用户成功", data=result)


@router.post("/list", response_model=BaseResponse[UserListResponse])
async def get_user_list(user_id: int = None, skip: int = 0, limit: int = 10):
    """
    获取用户列表

    - 需要认证
    - 支持分页
    """
    result = await UserService.get_user_list(skip=skip, limit=limit)
    return BaseResponse(code=0, message="获取用户列表成功", data=result)


# /me 路由
@router.post("/me", response_model=BaseResponse[UserResponse])
async def get_current_user():
    """
    获取当前登录用户的信息

    - 需要认证
    """
    result = await UserService.get_current_user()
    return BaseResponse(code=0, message="获取用户信息成功", data=result)


@router.post("/me/update", response_model=BaseResponse[UserResponse])
async def update_current_user(request: UpdateProfileRequest):
    """
    更新当前用户的个人信息

    - 需要认证
    - 可以更新用户名和邮箱（不包括密码）
    """
    result = await UserService.update_profile(request)
    return BaseResponse(code=0, message="更新个人信息成功", data=result)


@router.post("/me/change-password", response_model=BaseResponse[dict])
async def change_password(request: ChangePasswordRequest):
    """
    修改当前用户的密码

    - 需要认证
    - 需要验证当前密码
    """
    await UserService.change_password(request)
    return BaseResponse(code=0, message="修改密码成功", data={"success": True})


# 指定用户操作（使用 query 参数）
@router.post("/get", response_model=BaseResponse[UserResponse])
async def get_user(user_id: int):
    """
    获取单个用户

    - 需要认证
    - 参数: user_id (query parameter)
    """
    result = await UserService.get_user(user_id)
    return BaseResponse(code=0, message="获取用户成功", data=result)


@router.post("/update", response_model=BaseResponse[UserResponse])
async def update_user(user_id: int, request: UserUpdateRequest):
    """
    更新用户

    - 需要认证
    - 可以更新用户名、邮箱和密码
    - 参数: user_id (query parameter)
    """
    result = await UserService.update_user(user_id, request)
    return BaseResponse(code=0, message="更新用户成功", data=result)


@router.post("/delete", response_model=BaseResponse[dict])
async def delete_user(user_id: int):
    """
    删除用户

    - 需要认证
    - 参数: user_id (query parameter)
    """
    await UserService.delete_user(user_id)
    return BaseResponse(code=0, message="删除用户成功", data={"deleted": True})
