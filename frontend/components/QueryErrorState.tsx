import { ApiError } from '@/lib/apiTypes';

export default function QueryErrorState({ error }: { error: unknown }) {
  if (!(error instanceof ApiError)) {
    return <p className="text-red-600">请求失败，请稍后重试。</p>;
  }

  const messageByType: Record<ApiError['type'], string> = {
    BACKEND_UNAVAILABLE: '后端未启动或不可达：请先启动 uvicorn 并确认端口。',
    NOT_FOUND: '接口 404：请检查前端请求路径和后端路由是否一致。',
    TIMEOUT: '请求超时：网络较慢或后端响应过慢，请稍后重试。',
    SERVER_ERROR: '后端 500：请查看后端控制台日志定位具体错误。',
    NETWORK_ERROR: '网络错误：请确认本机网络连接与代理设置。',
    BAD_RESPONSE: '数据结构异常：后端返回字段不符合预期，请检查接口契约。',
    UNKNOWN: '未知错误：请查看浏览器控制台和后端日志。',
  };

  return <p className="text-red-600">{messageByType[error.type]}</p>;
}
