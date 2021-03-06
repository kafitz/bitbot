import logging
from observer import Observer
import config
import smtplib


def send_email(subject, message):
    _from = config.smtp_from
    to = config.smtp_to
    mime_message = """From: Python Arbitrage Script <%(_from)s>
To: <%(to)s>
Subject: %(subject)s

%(message)s
""" % locals()
    try:
        smtpObj = smtplib.SMTP(config.smtp_host)
        smtpObj.sendmail(config.smtp_from, [config.smtp_to], mime_message)
    except smtplib.SMTPException:
        logging.warn("Unable to send email")


class Emailer(Observer):
    def opportunity(self, profit, volume, buyprice, kask, sellprice, kbid, perc, weighted_buyprice, weighted_sellprice, available_volume, purchase_cap):
        if profit > config.profit_thresh and perc > config.perc_thresh:
            message = """profit: %f EUR with volume: %f BTC
buy at %.4f (%s) sell at %.4f (%s) ~%.2f%%
""" % (profit, volume, buyprice, kask, sellprice, kbid, perc)
            send_email(config.smtp_from, config.smtp_to, "", message)

if __name__ == "__main__":
    send_email("test", "hey!")
