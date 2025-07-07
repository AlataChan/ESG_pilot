# 使用Node.js官方镜像作为构建环境
FROM node:18-alpine as build

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./
COPY yarn.lock ./

# 安装依赖
RUN yarn install --frozen-lockfile

# 复制源代码
COPY . .

# 接受构建参数
ARG VITE_API_URL
ARG VITE_WS_URL

# 设置环境变量
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# 构建应用
RUN yarn build

# 使用Nginx作为生产环境服务器
FROM nginx:alpine

# 复制构建产物到Nginx目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制Nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]