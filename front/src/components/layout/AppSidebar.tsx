'use client';

import { Menu } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  MessageOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { usePathname, useRouter } from 'next/navigation';

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/dashboard/knowledge-bases', icon: <DatabaseOutlined />, label: '知识库' },
  { key: '/dashboard/chat', icon: <MessageOutlined />, label: 'AI问答' },
  { key: '/dashboard/profile', icon: <UserOutlined />, label: '个人中心' },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleMenuClick = ({ key }: { key: string }) => {
    router.push(key);
  };

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[pathname]}
      items={menuItems}
      onClick={handleMenuClick}
      style={{ height: '100%', borderRight: 0 }}
    />
  );
}
