'use client';

import { ConfigProvider, theme, App } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { StoreProvider } from '@/lib/store';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <StoreProvider>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
          components: {
            Layout: {
              headerBg: '#001529',
              siderBg: '#001529',
            },
          },
        }}
      >
        <App>{children}</App>
      </ConfigProvider>
    </StoreProvider>
  );
}
