import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if __name__ == '__main__':
    msg_from = 'sy_zjmail@cnooc.com.cn'  # 发送方邮箱
    to = ['sy_zjmail@cnooc.com.cn','1064988152@qq.com']  # 接受方邮箱

    msg = MIMEMultipart()
    conntent = "这是一封由python自动发送的邮件"
    msg.attach(MIMEText(conntent, 'plain', 'utf-8'))
    msg['Subject'] = "这个是邮件主题"

    # 发送方信息
    msg['From'] = msg_from
    s = smtplib.SMTP("10.139.32.25", timeout=30, port=25)
    # 开始发送
    s.sendmail(msg_from, to, msg.as_string())
    s.close()
    print("邮件发送成功")