import base64
from socket import socket, AF_INET, SOCK_STREAM
import ssl
import sys

MAIL_SERVERS = {'yandex.ru': ('smtp.yandex.ru', 465),
                'mail.ru': ('smtp.mail.ru', 465),
                'rambler.ru': ('smtp.rambler.ru ', 465),
                'gmail.com': ('smtp.gmail.com',465)}
BOUND = 'AAA170891tpFFKk__FV_KKKkkkjjwq'


class Client:
    def __init__(self):
        self.address_from, self.password, \
        self.address_to, self.subject, self.attachments = self.check_config()
        self.message = self.get_message()

    def start(self):
        context = ssl.create_default_context()
        for address in self.address_to:
            with socket(AF_INET, SOCK_STREAM) as tcp_socket:
                mail_server = MAIL_SERVERS[address.split('@')[1]]
                tcp_socket.connect(mail_server)
                with context.wrap_socket(tcp_socket, server_hostname=mail_server[0]) as stcp_socket:
                    print(stcp_socket.recv(1024).decode())
                    stcp_socket.send(f'EHLO {mail_server[0]}\r\n'.encode())  # Hello
                    print('Message after EHLO command:' + stcp_socket.recv(1024).decode())
                    base64_auth = base64.b64encode(
                        ('\x00' + self.address_from + '\x00' + self.password).encode())
                    auth_msg = 'AUTH PLAIN\r\n'.encode() + base64_auth + '\r\n'.encode()
                    stcp_socket.send(auth_msg)  # авторизация
                    print(stcp_socket.recv(1024).decode())
                    mail_from = f'MAIL FROM:<{self.address_from}>\r\n'
                    stcp_socket.send(mail_from.encode())  # почта отправителя
                    print('After MAIL FROM command: ' + stcp_socket.recv(1024).decode())
                    rcptTo = f'RCPT TO:<{address}>\r\n'
                    stcp_socket.send(rcptTo.encode())  # почта получателя
                    print('After RCPT TO command: ' + stcp_socket.recv(1024).decode())
                    stcp_socket.send('DATA\r\n'.encode())  # разрешение
                    print('After DATA command: ' + stcp_socket.recv(1024).decode())
                    subject = f'Subject: {self.subject}\r\n'
                    stcp_socket.send(subject.encode(encoding='windows-1251'))  # тема сообщения
                    stcp_socket.send(self.message.encode(encoding='utf-8'))  # Сообщение
                    stcp_socket.send('\r\n.\r\n'.encode())  # "закрыть" сообщение
                    print('Response after sending message body:' + stcp_socket.recv(1024).decode())
                    stcp_socket.send('QUIT\r\n'.encode())  # завершить сеанс
                    print(stcp_socket.recv(1024).decode())

    def get_message(self):
        '''
        формирует тело сообщения
        '''
        msg = f'MIME-Version: 1.0\r\nContent-type:multipart/mixed;boundary="{BOUND}"\n\r\n--{BOUND}\r\n'
        attachments = self.load_attachments()
        if attachments:
            for attachment in attachments:
                msg += attachment
        with open('message\msg.txt', 'r', encoding='utf-8') as f:
            text = f'Content-Type: text/plain; charset=utf-8\n\r\n'
            msg += text + ''.join(f.readlines()) + '\r\n--'+BOUND
        return msg

    @staticmethod
    def check_config():
        try:
            with open('message\conf.txt', 'r') as f:
                address_from = f.readline()[:-1].split(' ')[1]
                password = f.readline()[:-1].split(' ')[1]
                address_to = f.readline()[:-1].split(' ')
                address_to.pop(0)
                subject = f.readline()[:-1].partition(' ')[2]
                attachments = f.readline().split(' ')
                attachments.pop(0)
                return address_from, password, address_to, subject, attachments
        except Exception:
            print('данные были введены не верно, прочитайте readme, и введите данные корректно')
            sys.exit()

    def load_attachments(self):
        '''

        добавляет  в сообщение все MIME вложений
        '''
        result = []

        for attachment in self.attachments:
            try:
                with open(f'message\\{attachment}', "rb") as fil:
                    part =  base64.b64encode(fil.read()).decode(encoding='ascii')
                    attach = f'Content-Type:aplication/octet-stream;name="{attachment}"\r\nContent-Transfer-Encoding:base64\r\nContent-Disposition:attachment;filename:"{attachment}"'
                result.append(f'{attach}\n\r\n{part}\r\n--{BOUND}\r\n')
            except Exception:
                continue
        return result


if __name__ == '__main__':
    client = Client()
    client.start()
