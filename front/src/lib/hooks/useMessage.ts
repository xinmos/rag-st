import { App } from 'antd';

/**
 * 使用 App 组件的 message 实例
 * 替代静态方法 message.xxx()，以支持动态主题
 */
export function useMessage() {
  const { message } = App.useApp();
  return message;
}

/**
 * 使用 App 组件的 modal 实例
 */
export function useModal() {
  const { modal } = App.useApp();
  return modal;
}

/**
 * 使用 App 组件的 notification 实例
 */
export function useNotification() {
  const { notification } = App.useApp();
  return notification;
}
