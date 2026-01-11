'use client';

import { Breadcrumb, Dropdown, Avatar, Space } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAuth } from '@/lib/hooks';
import { useRouter } from 'next/navigation';
import type { MenuProps } from 'antd';

export function AppHeader() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const menuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => router.push('/dashboard/profile'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <div className="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
      <Breadcrumb
        items={[
          { title: '首页' },
          { title: '控制台' },
        ]}
      />
      <Space>
        <span className="text-gray-600">{user?.username}</span>
        <Dropdown menu={{ items: menuItems }} placement="bottomRight">
          <Avatar icon={<UserOutlined />} className="cursor-pointer" />
        </Dropdown>
      </Space>
    </div>
  );
}
