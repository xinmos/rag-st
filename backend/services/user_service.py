from typing import Optional, List

from common.context import get_request_context
from common.entity.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    LoginResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
)
from common.utils import create_access_token, hash_password, verify_password
from fastapi import HTTPException, status
from models.user import User


class UserService:
    """用户相关业务逻辑"""

    @staticmethod
    async def login(username: str, password: str) -> LoginResponse:
        """
        用户登录
        验证用户名和密码，返回 JWT token

        Args:
            username: 用户名
            password: 密码

        Returns:
            LoginResponse: 包含 token 和用户信息

        Raises:
            HTTPException: 用户名或密码错误
        """
        # 根据用户名查找用户
        users = await User.get_by_filter(username=username)
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        user = users[0]

        # 验证密码
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 生成 JWT token
        access_token = create_access_token(data={"sub": str(user.id)})

        # 构建响应
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            create_time=user.create_time
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    @staticmethod
    async def create_user(request: UserCreateRequest) -> UserResponse:
        """
        创建用户
        检查用户名和邮箱唯一性，创建新用户

        Args:
            request: 用户创建请求

        Returns:
            UserResponse: 创建的用户信息

        Raises:
            HTTPException: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_users = await User.get_by_filter(username=request.username)
        if existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_emails = await User.get_by_filter(email=request.email)
        if existing_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

        # 创建用户
        password_hash = hash_password(request.password)
        new_user = await User.create(
            username=request.username,
            email=request.email,
            password_hash=password_hash
        )

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            create_time=new_user.create_time
        )

    @staticmethod
    async def get_user_list(skip: int = 0, limit: int = 10) -> UserListResponse:
        """
        获取用户列表
        支持分页

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            UserListResponse: 用户列表和总数
        """
        users = await User.get_all(skip=skip, limit=limit)
        total = await User.count()

        user_responses = [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                create_time=user.create_time
            )
            for user in users
        ]

        return UserListResponse(total=total, items=user_responses)

    @staticmethod
    async def get_user(user_id: int) -> UserResponse:
        """
        获取单个用户

        Args:
            user_id: 用户ID

        Returns:
            UserResponse: 用户信息

        Raises:
            HTTPException: 用户不存在
        """
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            create_time=user.create_time
        )

    @staticmethod
    async def update_user(user_id: int, request: UserUpdateRequest) -> UserResponse:
        """
        更新用户
        可以更新用户名、邮箱和密码

        Args:
            user_id: 用户ID
            request: 用户更新请求

        Returns:
            UserResponse: 更新后的用户信息

        Raises:
            HTTPException: 用户不存在或用户名/邮箱已存在
        """
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 准备更新数据
        update_data = {}
        if request.username is not None:
            # 检查用户名是否被其他用户使用
            existing_users = await User.get_by_filter(username=request.username)
            if existing_users and existing_users[0].id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            update_data["username"] = request.username

        if request.email is not None:
            # 检查邮箱是否被其他用户使用
            existing_emails = await User.get_by_filter(email=request.email)
            if existing_emails and existing_emails[0].id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )
            update_data["email"] = request.email

        if request.password is not None:
            update_data["password_hash"] = hash_password(request.password)

        # 执行更新
        if update_data:
            updated_user = await User.update_by_id(user_id, **update_data)
            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                create_time=updated_user.create_time
            )

        # 如果没有需要更新的字段
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            create_time=user.create_time
        )

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            HTTPException: 用户不存在或删除失败
        """
        # 检查用户是否存在
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 执行删除
        deleted = await User.delete_by_id(user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )

        return True

    @staticmethod
    async def get_current_user() -> UserResponse:
        """
        获取当前登录用户的信息

        Returns:
            UserResponse: 当前用户信息

        Raises:
            HTTPException: 用户不存在或未登录
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        user = await User.get_by_id(ctx.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            create_time=user.create_time
        )

    @staticmethod
    async def update_profile(request: UpdateProfileRequest) -> UserResponse:
        """
        更新当前用户的个人信息（不包括密码）

        Args:
            request: 更新请求

        Returns:
            UserResponse: 更新后的用户信息

        Raises:
            HTTPException: 用户不存在或用户名/邮箱已存在
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        user_id = ctx.user_id
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 准备更新数据
        update_data = {}
        if request.username is not None:
            # 检查用户名是否被其他用户使用
            existing_users = await User.get_by_filter(username=request.username)
            if existing_users and existing_users[0].id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            update_data["username"] = request.username

        if request.email is not None:
            # 检查邮箱是否被其他用户使用
            existing_emails = await User.get_by_filter(email=request.email)
            if existing_emails and existing_emails[0].id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )
            update_data["email"] = request.email

        # 执行更新
        if update_data:
            updated_user = await User.update_by_id(user_id, **update_data)
            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                create_time=updated_user.create_time
            )

        # 如果没有需要更新的字段
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            create_time=user.create_time
        )

    @staticmethod
    async def change_password(request: ChangePasswordRequest) -> bool:
        """
        修改当前用户的密码

        Args:
            request: 修改密码请求，包含当前密码和新密码

        Returns:
            bool: 是否修改成功

        Raises:
            HTTPException: 未登录、用户不存在、当前密码错误
        """
        ctx = get_request_context()
        if ctx.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录"
            )

        user_id = ctx.user_id
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 验证当前密码
        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )

        # 更新密码
        password_hash = hash_password(request.new_password)
        await User.update_by_id(user_id, password_hash=password_hash)

        return True
