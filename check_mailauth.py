import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if __name__ == '__main__':
    msg_from = 'qihe.wei@cecport.com'  # 发送方邮箱
    passwd = 'Wqw@12315'  # 就是上面的授权码


    to = ['1064988152@qq.com']  # 接受方邮箱

    # 设置邮件内容
    # MIMEMultipart类可以放任何内容
    msg = MIMEMultipart()
    conntent = "这是一封由python自动发送的邮件"
    # 把内容加进去
    msg.attach(MIMEText(conntent, 'plain', 'utf-8'))

    # 设置邮件主题
    msg['Subject'] = "这个是邮件主题"

    # 发送方信息
    msg['From'] = msg_from

    # 开始发送

    s = smtplib.SMTP("10.1.100.219", timeout=30, port=25)
    # 通过SSL方式发送，服务器地址和端口
    #s = smtplib.SMTP_SSL("192.168.59.6", timeout=30, port=587)
    # 登录邮箱
    s.starttls()
    res = s.login(msg_from, passwd)
    print(res)
    # 开始发送
    s.sendmail(msg_from, to, msg.as_string())
    s.close()
    print("邮件发送成功")
