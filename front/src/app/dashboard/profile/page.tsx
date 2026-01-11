'use client';

import { useState } from 'react';
import { Card, Form, Input, Button, message, Tabs, Divider, Descriptions, Avatar } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/lib/hooks';
import { userApi } from '@/lib/api';

export default function ProfilePage() {
  const { user, refetch } = useAuth();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleProfileUpdate = async (values: { username?: string; email?: string }) => {
    setIsSubmitting(true);
    try {
      await userApi.updateProfile(values);
      message.success('更新成功');
      // Refetch user data
      refetch?.();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePasswordChange = async (values: {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
  }) => {
    setIsSubmitting(true);
    try {
      await userApi.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      message.success('密码修改成功');
      passwordForm.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const profileTabItems = [
    {
      key: 'profile',
      label: '基本信息',
      children: (
        <Card>
          <div className="flex items-center gap-4 mb-6">
            <Avatar size={80} icon={<UserOutlined />} />
            <div>
              <h2 className="text-xl font-semibold">{user?.username}</h2>
              <p className="text-gray-500">{user?.email}</p>
            </div>
          </div>

          <Divider />

          <Form
            form={profileForm}
            layout="vertical"
            initialValues={{
              username: user?.username,
              email: user?.email,
            }}
            onFinish={handleProfileUpdate}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
            >
              <Input />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={isSubmitting}>
                保存修改
              </Button>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
    {
      key: 'security',
      label: '安全设置',
      children: (
        <Card>
          <Form
            form={passwordForm}
            layout="vertical"
            onFinish={handlePasswordChange}
          >
            <Form.Item
              label="当前密码"
              name="currentPassword"
              rules={[{ required: true, message: '请输入当前密码' }]}
            >
              <Input.Password />
            </Form.Item>

            <Form.Item
              label="新密码"
              name="newPassword"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password />
            </Form.Item>

            <Form.Item
              label="确认新密码"
              name="confirmPassword"
              dependencies={['newPassword']}
              rules={[
                { required: true, message: '请确认新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('newPassword') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'));
                  },
                }),
              ]}
            >
              <Input.Password />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={isSubmitting}>
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
    {
      key: 'info',
      label: '账号信息',
      children: (
        <Card>
          <Descriptions column={1}>
            <Descriptions.Item label="用户ID">{user?.id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
            <Descriptions.Item label="注册时间">
              {user?.create_time
                ? new Date(user.create_time).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      ),
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">个人中心</h1>
      <Tabs items={profileTabItems} />
    </div>
  );
}
