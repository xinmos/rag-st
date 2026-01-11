'use client';

import { Layout } from 'antd';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { AppHeader } from '@/components/layout/AppHeader';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const { Sider, Content, Header } = Layout;

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <Layout style={{ height: '100vh', overflow: 'hidden' }}>
        <Sider width={240} theme="dark" style={{ height: '100vh', overflow: 'auto' }}>
          <AppSidebar />
        </Sider>
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
          <Header style={{ padding: 0, height: 64, lineHeight: '64px' }}>
            <AppHeader />
          </Header>
          <Content
            style={{
              margin: 0,
              height: 'calc(100vh - 64px)',
              overflow: 'auto',
              background: '#f0f2f5'
            }}
          >
            {children}
          </Content>
        </Layout>
      </Layout>
    </ProtectedRoute>
  );
}
