import boto3,urllib.parse
from botocore.exceptions import ClientError
from botocore.vendored import requests

def validate_token(token):
    return token == "ast-8+A683=NUIoenmSE¡?DG65bpQW3Ki54vrP93;_"
        
# Function to format the dictionary with the payload
def format_dic(dic):
    for key in dic:
        dic[key] = dic[key][0]
    if 'history' not in dic:
        dic['history'] = ""
    return dic

def send_email(recipient, subject, body, body_html):
  # This address must be verified with Amazon SES.
  SENDER = "couteda@denodo.com"
 
  # If your account is still in the sandbox, this address must be verified.
  RECIPIENT = recipient
 
  # Specify a configuration set. If you do not want to use a configuration
  # set, comment the following variable, and the 
  # ConfigurationSetName=CONFIGURATION_SET argument below.
  # CONFIGURATION_SET = "ConfigSet"
 
  # The AWS Region you're using for Amazon SES.
  AWS_REGION = "us-east-1"
 
  # The subject line for the email.
  SUBJECT = subject
 
  # The email body for recipients with non-HTML email clients.
  BODY_TEXT = body
             
  # The HTML body of the email.
  BODY_HTML = body_html
 
  # The character encoding for the email.
  CHARSET = "UTF-8"
 
  # Create a new SES resource and specify a region.
  client = boto3.client('ses',region_name=AWS_REGION)
 
  # Try to send the email.
  try:
    #Provide the contents of the email.
    response = client.send_email(
    Destination={
      'ToAddresses': [
                   RECIPIENT,
               ],
           },
    Message={
      'Body': {
                'Html': {
                       'Charset': CHARSET,
                       'Data': BODY_HTML,
                   },
                   'Text': {
                       'Charset': CHARSET,
                       'Data': BODY_TEXT,
                   },
               },
               'Subject': {
                   'Charset': CHARSET,
                   'Data': SUBJECT,
               },
           },
    Source=SENDER,
           # If you are not using a configuration set, comment or delete the
           # following line
           # ConfigurationSetName=CONFIGURATION_SET,
  )
  except ClientError as e:
       print(e.response['Error']['Message'])
       return(e.response['Error']['Message'] + "\n")
  else:
      print("Email sent! Message ID:"+ response['MessageId'])
      return("Email sent!" + "\n" + "Message ID: "+ response['MessageId'] + "\n")

def lambda_handler(event, context):
  #parsing the data from x-www-form-urlencoded to a dict
  data = event['body']
  payload = format_dic(urllib.parse.parse_qs(data))
  print('Event:', payload)
  print('Context:', str(context))
  
  #Validating token
  if not validate_token(payload['Ftoken']):
      print("Invalid token in message")
      return{"statusCode": 401, "body": "Unauthorized!"}
  
  executionId = payload['executionId']
  print(executionId)
  
  #subject for emails
  email_subject = '[DAPS] Action Required: Approval Request from ' + payload['employee'].split("@")[0] + ' [Id: ' + executionId + ']'
  
  # Compose email to manager
  if payload['isManager'] == "true":
    recipient = payload['employee']
    email_body = """
        Hello Manager,
        Select to Approve or Reject the following request from {email}:
        {Frequest}
        Opportunity - {Fopportunity}
        
        Details:
        Service: {Fservice}
        Public IP: {Fpublicip}
        Time Start: {Ftimestart}
        Time End: {Ftimeend}

        Approve:
        {approve}

        Reject:
        {reject}
        
        history:
        {history}
        
        This email was automatically sent by:
        Denodo Automated Provisioning System (DAPS)
        """.format(
            email=payload['employee'],
            name=payload['employee'].split("@")[0],
            approve=payload['approve'],
            reject=payload['reject'],
            Fservice=payload['Fservice'],
            Fpublicip=payload['Fpublicip'],
            Ftimestart=payload['Ftimestart'],
            Ftimeend=payload['Ftimeend'],
            Frequest=payload['Frequest'],
            Fopportunity=payload['Fopportunity'],
            history=(payload['history']  + payload['employee'].split("@")[0] + ": " + payload['discussion'].strip() + "<br></br>").replace("<br></br>","\n")
        )
        # html body
    email_body1 = """
        <html>
            <head></head>
            <body>
                <br>Hello Manager,</br>
                <br>Select to Approve or Reject the following request from {email}:</br>
                <br>{Frequest}</br>
                <br>Opportunity - {Fopportunity}</br>
                <br></br>
                <br>Details:</br>
                <br>Service: {Fservice}</br>
                <br>Public IP: {Fpublicip}</br>
                <br>Time Start: {Ftimestart}</br>
                <br>Time End: {Ftimeend}</br>
                <br></br>
                <br>Approve:</br>
                <a href = {approve} target= "_blank"> Link to approve the deploy</a>
                <br></br>
                <br>Reject:</br>
                <a href = {reject} target= "_blank"> Link to reject the deploy</a>
                <br></br><br></br>
                <br> Messages: </br>
                <br>{history}</br>
                <br></br>
                <form action =  https://izxlneci59.execute-api.us-east-1.amazonaws.com/mock/discussion method = "post">
                    <label>If you want to consult anything with {email} before approving or rejecting write it in the box below and press submit</label><br></br>
                    <textarea id="discussion" name= "discussion" rows= "5" cols= "100" > </textarea>
                    <input id="employee" name="employee" type="hidden" value="{email}"></input>
                    <input id= "manager" name="manager" type="hidden" value="couteda@denodo.com"></input>
                    <input id= "approve" name = "approve" type= "hidden" value="{approve}"></input>
                    <input id= "reject" name ="reject" type="hidden" value="{reject}"></input>
                    <input id= "Fservice" name ="Fservice" type="hidden" value="{Fservice}"></input>
                    <input id= "Fpublicip" name ="Fpublicip" type="hidden" value="{Fpublicip}"></input>
                    <input id= "Ftimestart" name ="Ftimestart" type="hidden" value="{Ftimestart}"></input>
                    <input id= "Ftimeend" name ="Ftimeend" type="hidden" value="{Ftimeend}"></input>
                    <input id= "Ftoken" name ="Ftoken" type="hidden" value="{Ftoken}"></input>
                    <input id= "Frequest" name ="Frequest" type="hidden" value="{Frequest}"></input>
                    <input id= "Fopportunity" name ="Fopportunity" type="hidden" value="{Fopportunity}"></input>
                    <input id= "executionId" name ="executionId" type="hidden" value="{executionId}"></input>
                    <input id="history" name="history" type="hidden" value="{history}"></input>
                    <input id= "isManager" name ="isManager" type="hidden" value="false"></input>
                    <br></br>
                    <input type="submit" value="Submit"></input>
                </form>
                <br></br>
                <br>This email was automatically sent by:</br>
                <br><footer>Denodo Automated Provisioning System (DAPS)</footer></p></br>
            </body>
        </html>
        """.format(
            email=payload['employee'],
            name=payload['employee'].split("@")[0],
            approve=payload['approve'],
            reject=payload['reject'],
            Fservice=payload['Fservice'],
            Fpublicip=payload['Fpublicip'],
            Ftimestart=payload['Ftimestart'],
            Ftimeend=payload['Ftimeend'],
            Frequest=payload['Frequest'],
            Ftoken=payload['Ftoken'],
            Fopportunity=payload['Fopportunity'],
            history = payload['history']  + payload['employee'].split("@")[0] + ": " + payload['discussion'].strip() + "<br></br>",
            executionId= executionId
        )
  else:
    recipient = "couteda@denodo.com" 
    #Compose email for employees
    email_body ="""
        Hello {name},
        
        The managers started a discussion for your request
        
        Messages:
        {history}
        
        This email was automatically sent by:
        Denodo Automated Provisioning System (DAPS)
    """.format(
        name=payload['employee'].split("@")[0],
        history = (payload['history']  + "Manager: " + payload['discussion'].strip() + "<br></br>").replace("<br></br>","\n")
        )
    email_body1 ="""
        <html>
            <head></head>
            <body>
                <br>Hello {name},</br>
                <br></br>
                <br> The managers started a discussion for your request </br>
                <br></br>
                <br> Messages: </br>
                <br>{history}</br>
                <br></br>
                <form action =  https://izxlneci59.execute-api.us-east-1.amazonaws.com/mock/discussion method = "post">
                    <label>please submit your response in box below</label><br></br>
                    <textarea id="discussion" name= "discussion" rows= "5" cols= "100" > </textarea>
                    <input id="employee" name="employee" type="hidden" value="{email}"></input>
                    <input id= "manager" name="manager" type="hidden" value="couteda@denodo.com"></input>
                    <input id= "approve" name = "approve" type= "hidden" value="{approve}"></input>
                    <input id= "reject" name ="reject" type="hidden" value="{reject}"></input>
                    <input id= "Fservice" name ="Fservice" type="hidden" value="{Fservice}"></input>
                    <input id= "Fpublicip" name ="Fpublicip" type="hidden" value="{Fpublicip}"></input>
                    <input id= "Ftimestart" name ="Ftimestart" type="hidden" value="{Ftimestart}"></input>
                    <input id= "Ftimeend" name ="Ftimeend" type="hidden" value="{Ftimeend}"></input>
                    <input id= "Ftoken" name ="Ftoken" type="hidden" value="{Ftoken}"></input>
                    <input id= "Frequest" name ="Frequest" type="hidden" value="{Frequest}"></input>
                    <input id= "Fopportunity" name ="Fopportunity" type="hidden" value="{Fopportunity}"></input>
                    <input id= "executionId" name ="executionId" type="hidden" value="{executionId}"></input>
                    <input id="history" name="history" type="hidden" value="{history}"></input>
                    <input id= "isManager" name ="isManager" type="hidden" value="true"></input>
                    <br></br>
                    <input type="submit" value="Submit"></input>
                </form>
                <br></br>
                <br>This email was automatically sent by:</br>
                <br><footer>Denodo Automated Provisioning System (DAPS)</footer></p></br>
            </body>
        </html>
    """.format(
            email=payload['employee'],
            name=payload['employee'].split("@")[0],
            approve=payload['approve'],
            reject=payload['reject'],
            Fservice=payload['Fservice'],
            Fpublicip=payload['Fpublicip'],
            Ftimestart=payload['Ftimestart'],
            Ftimeend=payload['Ftimeend'],
            Ftoken=payload['Ftoken'],
            Frequest=payload['Frequest'],
            Fopportunity=payload['Fopportunity'],
            history = payload['history']  + "Manager: " + payload['discussion'].strip() + "<br></br>",
            executionId= executionId
            )
  response = send_email(recipient, email_subject, email_body, email_body1)
  print('done')
  return{"statusCode": 200, "body": response + "message:" +payload['discussion']}