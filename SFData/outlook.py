import win32com.client as win32
#https://stackoverflow.com/questions/6332577/send-outlook-email-via-python

class emailMessage():
    def __init__(self, subject, toAddress, htmlBody=None, attachmentPath=None, emailbody=None):
        self.subject = subject
        self.emailbody = emailbody
        #self.recipient = recipient
        self.toAddress = toAddress
        self.htmlBody = htmlBody
        self.attachmentPath = attachmentPath
        self.outlook = win32.Dispatch('outlook.application')

    def send(self):
        mail = self.outlook.CreateItem(0)
        mail.To = self.toAddress
        mail.Subject = self.subject
        if self.emailbody != None:
            mail.Body = self.emailbody
        if self.htmlBody != None:
            mail.HTMLBody = self.htmlBody #this field is optional
        # To attach a file to the email (optional):
        if self.attachmentPath != None:
            attachment  = self.attachmentPath
            mail.Attachments.Add(attachment)
        mail.Send()
