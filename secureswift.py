import asyncio
import struct
import socket
import ssl
import logging
from typing import List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SOCKS5Server:
    def __init__(self, host: str, port: int, allowed_ips: List[str], cert_file: str, key_file: str):
        self.host = host
        self.port = port
        self.allowed_ips = allowed_ips
        self.cert_file = cert_file
        self.key_file = key_file

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip = writer.get_extra_info('peername')[0]
        
        if client_ip not in self.allowed_ips:
            logger.warning(f"未授权的访问尝试，来自IP: {client_ip}")
            writer.close()
            await writer.wait_closed()
            return
        
        try:
            # SOCKS5 握手
            version, nmethods = struct.unpack("!BB", await reader.read(2))
            methods = await reader.read(nmethods)
            writer.write(b"\x05\x00")
            await writer.drain()
            
            # 获取请求详情
            version, cmd, _, address_type = struct.unpack("!BBBB", await reader.read(4))
            if address_type == 1:  # IPv4
                addr = socket.inet_ntoa(await reader.read(4))
            elif address_type == 3:  # 域名
                addr_len = (await reader.read(1))[0]
                addr = (await reader.read(addr_len)).decode('utf-8')
            else:
                writer.close()
                await writer.wait_closed()
                return
            
            port = struct.unpack('!H', await reader.read(2))[0]
            
            if cmd == 1:  # CONNECT
                try:
                    remote_reader, remote_writer = await asyncio.open_connection(addr, port)
                    bind_address = remote_writer.get_extra_info('sockname')
                    logger.info(f"连接到 {addr}:{port}")
                    reply = struct.pack("!BBBBIH", 5, 0, 0, 1, 
                                        struct.unpack("!I", socket.inet_aton(bind_address[0]))[0],
                                        bind_address[1])
                except Exception as e:
                    logger.error(f"无法连接到远程服务器 {addr}:{port} - {e}")
                    reply = struct.pack("!BBBBIH", 5, 5, 0, 1, 0, 0)
            else:
                reply = struct.pack("!BBBBIH", 5, 7, 0, 1, 0, 0)
            
            writer.write(reply)
            await writer.drain()
            
            if reply[1] == 0 and cmd == 1:
                await self.proxy_data(reader, writer, remote_reader, remote_writer)
            else:
                writer.close()
                await writer.wait_closed()
                
        except Exception as e:
            logger.error(f"处理客户端时出错: {e}")
            writer.close()
            await writer.wait_closed()

    async def proxy_data(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter,
                         remote_reader: asyncio.StreamReader, remote_writer: asyncio.StreamWriter):
        async def forward(src: asyncio.StreamReader, dst: asyncio.StreamWriter):
            try:
                while True:
                    data = await asyncio.wait_for(src.read(8192), timeout=300)  # 5分钟超时
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except asyncio.TimeoutError:
                logger.info("连接空闲超时")
            except Exception as e:
                logger.error(f"转发错误: {e}")
            finally:
                dst.close()
                await dst.wait_closed()

        await asyncio.gather(
            forward(client_reader, remote_writer),
            forward(remote_reader, client_writer)
        )

    async def start(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port, ssl=ssl_context
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f'SSL加密的SOCKS5代理服务器正在运行，地址：{addr}')
        logger.info(f"允许的IP地址: {', '.join(self.allowed_ips)}")
        
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    HOST = '0.0.0.0'  # 监听所有网络接口
    PORT = 59485      # 端口号
    ALLOWED_IPS = [
        '192.168.0.101',
        '192.168.0.122',
        '192.168.0.102',
        '192.168.0.106',
        '192.168.0.107',
        '192.168.0.108',
        '192.168.0.110',
        '192.168.1.101',
        '192.168.1.110',
        '192.168.19.200',
    ]
    CERT_FILE = "cert.pem"
    KEY_FILE = "key.pem"
    
    server = SOCKS5Server(HOST, PORT, ALLOWED_IPS, CERT_FILE, KEY_FILE)
    asyncio.run(server.start())