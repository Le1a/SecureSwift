# 🚀 SecureSwift

## 🛡️ 高性能、安全的 SOCKS5 代理服务器

SecureSwift 是一个强大、高效且安全的 SOCKS5 代理服务器，采用 Python 异步编程和 SSL 加密，为您的网络通信提供卓越的性能和安全保障。

### ✨ 主要特性

- 🔒 SSL 加密保护所有通信
- 🚄 基于 asyncio 的高性能异步架构
- 🔍 IP 白名单功能，增强访问控制
- 📊 详细的日志记录，便于监控和故障排查
- 🔧 易于配置和部署
- 🌐 支持 IPv4 和域名解析
- 🔀 可与 stunnel 和 SwitchyOmega 配合使用，实现更灵活的代理设置

### 🛠️ 安装

1. 克隆仓库：
```
git clone https://github.com/yourusername/SecureSwift.git
```
2. 进入项目目录：
```
cd SecureSwift
```
### 📝 配置

1. 准备 SSL 证书，使用如下命令生成私钥文件和自签名证书
- `openssl genpkey -algorithm RSA -out key.pem`
- `openssl req -new -x509 -key key.pem -out cert.pem -days 365`

2. 编辑 `secureswift.py`：
- 在 `ALLOWED_IPS` 列表中添加允许访问的 IP 地址

3. 在macOS上创建一个 stunnel.conf 文件，内容如下：
```
[socks]
client = yes
accept = 127.0.0.1:1088
connect = 192.168.0.122:59485
cert = cert.pem
key = key.pem
CAfile = cert.pem
verify = 2
```

4. SwitchyOmega 配置
设置代理协议为 SOCKS5，地址为 127.0.0.1，端口为 1088（与 stunnel 配置中的 accept 端口一致）。

现在，您可以通过 SwitchyOmega 轻松切换代理，流量将通过 stunnel 加密后发送到 SecureSwift 服务器。

### 🚀 运行

执行以下命令启动 SecureSwift：
```
python3 secureswift.py
```
